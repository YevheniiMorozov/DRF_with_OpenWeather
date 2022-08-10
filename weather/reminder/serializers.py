from rest_framework import serializers

from .models import City, Subscribe, WeatherUser, Weather


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(max_length=20, min_length=8, write_only=True)

    class Meta:
        model = WeatherUser
        fields = ['username', "email", "password"]

    def create(self, validated_data):
        return WeatherUser.objects.create_user(**validated_data)


class CitySerializers(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ["name"]


class SubscribeSerializer(serializers.ModelSerializer):
    city = CitySerializers(read_only=True)

    class Meta:
        model = Subscribe
        fields = ["city", 'notification']


class WeatherSerializer(serializers.ModelSerializer):
    city = CitySerializers(read_only=True)

    class Meta:
        model = Weather
        fields = ['city', "temperature", 'feels_like', "weather_description", "src_img"]
