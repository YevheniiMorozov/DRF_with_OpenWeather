from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator


class WeatherUser(AbstractUser):
    email = models.EmailField(unique=True)


class City(models.Model):
    name = models.CharField(max_length=30, unique=True)


class Subscribe(models.Model):
    user = models.ForeignKey(WeatherUser, on_delete=models.CASCADE)
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    notification = models.PositiveIntegerField(default=2, validators=[MaxValueValidator(24)])


class Weather(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    temperature = models.FloatField()
    feels_like = models.FloatField()
    weather_description = models.CharField(max_length=100)
    src_img = models.CharField(max_length=150)

    class Meta:
        ordering = ["-id"]
