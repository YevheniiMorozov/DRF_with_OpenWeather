from datetime import datetime, timedelta

from celery import shared_task

from decouple import config

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from .views import get_weather
from .models import Subscribe, Weather, City
from collections import defaultdict


# python -m celery -A weather worker


@shared_task
def update_weather():
    cities = [city for city in City.objects.all()]
    weather = []
    for city in cities:
        data = get_weather(city.name)
        weather.append(Weather(
            city=city,
            temperature=data['main']["temp"],
            feels_like=data['main']["feels_like"],
            weather_description=data['weather'][0]["description"],
            src_img=f"http://openweathermap.org/img/wn/{data['weather'][0]['icon']}@2x.png"
        ))
    Weather.objects.bulk_create(weather)
    print("updated")


@shared_task
def send_mail():
    start = 0
    for elements in range(start+1, Subscribe.objects.count(), 100):
        subs = [(sub.user.email, sub.city.name, sub.notification, sub.last_sent_time)
                for sub in Subscribe.objects.select_related("user", "city").extra(where=[
                f"user__id > '{start}', user__id <= '{elements + start}'"
            ])]
        start += 100

        weather = {weather.city.name: weather for weather in Weather.objects.select_related("city").all()}

        sub_dict = defaultdict(list)
        for email, city, notification, last_sent in subs:
            sub_dict[email].append((weather[city], notification, last_sent))

        for email, info in sub_dict.items():
            mail_body = ''
            for weather, notification, last_sent in info:
                if last_sent + timedelta(hours=notification) < datetime.now():
                    continue
                mail_body += f'''<br>
                <strong>{weather.city}</strong><br>
                Temperature: {weather.temperature}<br>
                Feels like: {weather.feels_like}<br>
                Description: {weather.weather_description}<br'''
                Weather.objects.filter(user__email=email, city__name=weather.city).update(
                    last_sent=datetime.now()
                )

            send_grid = SendGridAPIClient(config("SENDGRID_API_KEY"))
            message = Mail(
                from_email="gml.for.a.work@gmail.com",
                to_emails=email,
                subject="Notification weather in cities",
                html_content=mail_body
            )
            send_grid.send(message)
            print("Mail sending: ", mail_body)
