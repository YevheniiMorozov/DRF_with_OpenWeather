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
    city = serializers.CharField(source="city.name")

    class Meta:
        model = Subscribe
        fields = ["city", 'notification']

    def create(self, validated_data):
        city_name = validated_data.get("city")['name']
        notification = validated_data.get("notification")
        user = self.context["request"].user
        if city_name.isdigit():
            raise serializers.ValidationError("'city' must be a string")
        if City.objects.filter(name=city_name).exists():
            city = City.objects.get(name=city_name)
            if Subscribe.objects.filter(user=user, city=city).exists():
                raise serializers.ValidationError("Notification is already exists")
            sub = Subscribe.objects.create(user=user, city=city,
                                           notification=notification)
            return sub
        raise serializers.ValidationError("You must add city to create the sub")

    def update(self, instance, validated_data):
        city_name = validated_data.get("city")['name']
        notification = validated_data.get("notification")
        user = self.context["request"].user
        if not Subscribe.objects.filter(city__name=city_name).exists():
            raise serializers.ValidationError("This sub doesn`t exists")
        sub = Subscribe.objects.filter(user=user, city__name=city_name).first()
        sub.notification = notification
        sub.save()
        return sub


class WeatherSerializer(serializers.ModelSerializer):
    city = CitySerializers(read_only=True)

    class Meta:
        model = Weather
        fields = ['city', "temperature", 'feels_like', "weather_description", "src_img"]
