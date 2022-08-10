from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse

from .models import WeatherUser, Weather, City, Subscribe


class BasicTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = WeatherUser.objects.create_user(email="123@123.com", password="password", username="testuser")
        self.first_city = City.objects.create(name="London")
        self.second_city = City.objects.create(name="Киев")
        self.weather_1 = Weather.objects.create(city=self.first_city,
                                                temperature=37.7,
                                                feels_like=36.6,
                                                weather_description="permanently snowing",
                                                src_img="sun_img")
        self.weather_2 = Weather.objects.create(city=self.second_city,
                                                temperature=26.1,
                                                feels_like=26.2,
                                                weather_description="sunny",
                                                src_img="just_an_img")
        self.sub1 = Subscribe.objects.create(user=self.user, city=self.first_city, notification=2)

    def test_user(self):
        self.assertEqual(WeatherUser.objects.count(), 1)


class ModelTestCase(BasicTestCase):

    def test_models(self):
        user = WeatherUser.objects.get(username="testuser")
        self.assertEqual(user.email, '123@123.com')

        self.assertEqual(Subscribe.objects.count(), 1)
        self.assertEqual(City.objects.count(), 2)

        weather_1 = Weather.objects.get(city__name="London")
        self.assertEqual(weather_1.temperature, 37.7)
        self.assertEqual(weather_1.feels_like, 36.6)
        self.assertEqual(weather_1.weather_description, 'permanently snowing')
        self.assertEqual(weather_1.src_img, "sun_img")

        weather_2 = Weather.objects.get(city__name="Киев")
        self.assertEqual(weather_2.temperature, 26.1)
        self.assertEqual(weather_2.feels_like, 26.2)
        self.assertEqual(weather_2.weather_description, 'sunny')
        self.assertEqual(weather_2.src_img, "just_an_img")


class ViewTestCase(BasicTestCase):

    def test_register(self):
        response = self.client.post(reverse("register"), {"username": "user1",
                                                          "email": "321@123.com",
                                                          "password": "password1"}, follow=True)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, {"username": "user1", "email": "321@123.com"})

    def test_subscription(self):
        self.client.force_login(user=self.user)

        response = self.client.get(reverse('sub'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "123@123.com")

        response = self.client.post(reverse('sub'), {"city": "Киев", 'notification': 3}, follow=True)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['notification'], 3)
        self.assertEqual(Subscribe.objects.count(), 2)

        response = self.client.put(reverse('sub'), {"city": "Киев", 'notification': 6}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['notification'], 6)

        response = self.client.delete(reverse('sub'), {"city": "Киев"}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, "Deleted")
        self.assertEqual(Subscribe.objects.count(), 1)
        self.assertEqual(City.objects.count(), 1)

        self.client.logout()

    def test_city_weather(self):
        self.client.force_login(user=self.user)

        response = self.client.get(reverse("city_weather", kwargs={"city_name": 'London'}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"city": {"name": "London"},
                                         "temperature": 37.7,
                                         "feels_like": 36.6,
                                         "weather_description": "permanently snowing",
                                         "src_img": "sun_img"})

        response = self.client.get(reverse("city_weather", kwargs={"city_name": 'Lviv'}))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data, "City does not exists, but you can add it")

        response = self.client.post(reverse("city_weather", kwargs={"city_name": 'London'}))
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data, "City is already exists")

        response = self.client.post(reverse("city_weather", kwargs={"city_name": 'Lviv'}))
        self.assertEqual(response.status_code, 201)
