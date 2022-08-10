import requests
from decouple import config

from django.core.management.base import BaseCommand, CommandError

from reminder.models import City, Weather


def get_weather(city):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={config('WEATHER_API_KEY')}&units=metric"
    return requests.get(url).json()


def add_data():
    cities_names = ['Kyiv', "London", "Texas", "Warsaw", "Paris"]

    cities = [City(name=element) for element in cities_names]

    City.objects.bulk_create(cities)

    weather = []
    for element in cities_names:
        data = get_weather(element)
        weather.append(Weather(city=City.objects.get(name=element),
                               temperature=data['main']["temp"],
                               feels_like=data['main']["feels_like"],
                               weather_description=data['weather'][0]["description"],
                               src_img=f"http://openweathermap.org/img/wn/{data['weather'][0]['icon']}@2x.png"
                               ))
    Weather.objects.bulk_create(weather)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("add_data", nargs='+', type=str)

    def handle(self, *args, **options):
        City.objects.all().delete()
        Weather.objects.all().delete()

        if options['add_data']:
            add_data()
            self.stdout.write(self.style.SUCCESS("Successfully create"))
        else:
            CommandError("Error")
