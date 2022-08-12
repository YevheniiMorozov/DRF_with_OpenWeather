import json

from celery import shared_task
from decouple import config

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from django.utils import timezone
from django_celery_beat.models import PeriodicTask, IntervalSchedule


from .views import get_weather
from .models import Subscribe, Weather


@shared_task(name="update_weather")
def update_weather(city):
    data = get_weather(city)
    Weather.objects.filter(city__name=city).update(
        temperature=data['main']["temp"],
        feels_like=data['main']["feels_like"],
        weather_description=data['weather'][0]["description"],
        src_img=f"http://openweathermap.org/img/wn/{data['weather'][0]['icon']}@2x.png"
    )


@shared_task(name="send_mail")
def send_mail(sub_id):
    sub = Subscribe.objects.get(id=sub_id)
    weather = Weather.objects.get(city=sub.city)
    mail_body = f'''
    <strong>{weather.city}</strong><br>
    Temperature: {weather.temperature}<br>
    Feels like: {weather.feels_like}<br>
    Description: {weather.weather_description}<br'''

    send_grid = SendGridAPIClient(config("SENDGRID_API_KEY"))
    message = Mail(
        from_email="gml.for.a.work@gmail.com",
        to_emails=sub.user.email,
        subject="Notification weather in cities",
        html_content=mail_body
    )
    send_grid.send(message)


def update_weather_task(city):
    schedule, created = IntervalSchedule.objects.get_or_create(every=1, period=IntervalSchedule.HOURS)
    task = PeriodicTask.objects.create(
        name=f"update weather in {city}",
        task="update_weather",
        interval=schedule,
        args=json.dumps([city]),
        start_time=timezone.now()
    )
    task.save()


def delete_weather_task(city):
    task = PeriodicTask.objects.get(name=f"update weather in {city}")
    task.delete()


def send_email_create_task(request):
    city = request.data.get('city')
    user = request.user
    sub = Subscribe.objects.get(city__name=city, user=user)
    schedule, created = IntervalSchedule.objects.get_or_create(every=sub.notification, period=IntervalSchedule.HOURS)
    task = PeriodicTask.objects.create(
        name=f'send weather in {city} to {user.email}',
        task='send_mail',
        interval=schedule,
        args=json.dumps([sub.id]),
        start_time=timezone.now()
    )
    task.save()


def send_email_edit_task(request):
    city = request.data.get('city')
    user = request.user
    notification = request.data.get('notification')
    task = PeriodicTask.objects.get(name=f'send weather in {city} to {user.email}')
    task.interval.every = notification
    task.interval.save()
    task.save()


def send_email_delete_task(request):
    city = request.data.get('city')
    user = request.user
    task = PeriodicTask.objects.get(name=f'send weather in {city} to {user.email}')
    task.delete()