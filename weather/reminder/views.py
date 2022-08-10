import requests
import trafaret as tr

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny, IsAuthenticated
from rest_framework.generics import GenericAPIView
from rest_framework import response, status

from .models import Subscribe, City, Weather
from .serializers import UserSerializer, SubscribeSerializer, WeatherSerializer

from decouple import config


def get_weather(city):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={config('WEATHER_API_KEY')}&units=metric"
    if requests.get(url).status_code == 200:
        return requests.get(url).json()
    return None


class RegisterAPIView(GenericAPIView):

    permission_classes = [AllowAny]
    serializer_class = UserSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return response.Response(serializer.data, status=status.HTTP_201_CREATED)
        return response.Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserSubscribeAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        subscribe = Subscribe.objects.filter(user=request.user).all()[:100]
        serializer = SubscribeSerializer(subscribe, many=True)
        return response.Response({f"{request.user.email}": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request):
        city_name = request.data["city"] if request.data else None
        notification = request.data["notification"] if request.data else None
        if not (city_name and notification):
            return response.Response("Add 'city' and 'notification' to create sub", status=status.HTTP_400_BAD_REQUEST)
        try:
            tr.String().check(city_name)
        except tr.DataError:
            return response.Response("'city' must be a string", status=status.HTTP_400_BAD_REQUEST)
        try:
            tr.Int().check(notification)
        except tr.DataError:
            return response.Response("'notification' must be an integer", status=status.HTTP_400_BAD_REQUEST)
        if City.objects.filter(name=city_name).exists():
            city = City.objects.get(name=city_name)
        else:
            city = City.objects.create(name=city_name)
        if Subscribe.objects.filter(user=request.user, city=city).exists():
            return response.Response("Notification is already exists", status=status.HTTP_204_NO_CONTENT)
        new_sub = Subscribe.objects.create(
            user=request.user, city=city, notification=notification
        )
        new_sub.save()
        serializer = SubscribeSerializer(new_sub)
        return response.Response(serializer.data, status=status.HTTP_201_CREATED)

    def put(self, request):
        notification = request.data['notification']
        city_name = request.data["city"]
        try:
            tr.String().check(city_name)
        except tr.DataError:
            return response.Response("'city' must be a string", status=status.HTTP_400_BAD_REQUEST)
        try:
            tr.Int().check(notification)
        except tr.DataError:
            return response.Response("'notification' must be an integer", status=status.HTTP_400_BAD_REQUEST)
        if not Subscribe.objects.filter(city__name=city_name).exists():
            return response.Response("This sub doesn`t exists", status=status.HTTP_400_BAD_REQUEST)
        sub = Subscribe.objects.filter(user=request.user, city__name=city_name).first()
        sub.notification = notification
        sub.save()
        serializer = SubscribeSerializer(sub)
        return response.Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request):
        city_name = request.data["city"]
        try:
            tr.String().check(city_name)
        except tr.DataError:
            return response.Response("'city' must be a string", status=status.HTTP_400_BAD_REQUEST)
        if not City.objects.filter(name=city_name).exists():
            return response.Response("City does not exists", status=status.HTTP_404_NOT_FOUND)
        Subscribe.objects.filter(user=request.user, city__name=city_name).delete()
        if not Subscribe.objects.filter(city__name=city_name).exists():
            Weather.objects.filter(city__name=city_name).all().delete()
            City.objects.filter(name=city_name).delete()
        return response.Response("Deleted", status=status.HTTP_200_OK)


class WeatherAPIView(APIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get(self, request, **kwargs):
        city_name = kwargs.get("city_name")
        if City.objects.filter(name=city_name).exists():
            weather_in_city = Weather.objects.filter(city__name=city_name).first()
            serializer = WeatherSerializer(weather_in_city)
            print(serializer.data)
            return response.Response(data=serializer.data, status=status.HTTP_200_OK)
        return response.Response("City does not exists, but you can add it", status=status.HTTP_404_NOT_FOUND)

    def post(self, request, **kwargs):
        city_name = kwargs.get("city_name")
        if City.objects.filter(name=city_name).exists():
            return response.Response("City is already exists", status=status.HTTP_204_NO_CONTENT)
        data = get_weather(city_name)
        if data:
            city = City.objects.create(name=city_name)
            weather_city = Weather.objects.create(
                city=city,
                temperature=data['main']["temp"],
                feels_like=data['main']["feels_like"],
                weather_description=data['weather'][0]["description"],
                src_img=f"http://openweathermap.org/img/wn/{data['weather'][0]['icon']}@2x.png"
            )
            serializer = WeatherSerializer(weather_city)
            return response.Response(data=serializer.data, status=status.HTTP_201_CREATED)
        return response.Response("Invalid data, try again", status=status.HTTP_400_BAD_REQUEST)
