from django.urls import path, include
from .views import *
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from rest_framework import urls


urlpatterns = [
    path("drf-auth/", include("rest_framework.urls")),
    path("register/", RegisterAPIView.as_view(), name='register'),
    path("user_sub/", UserSubscribeAPIView.as_view(), name='sub'),
    path("weather/<city_name>/", WeatherAPIView.as_view(), name='city_weather'),
    path("token/", TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path("token/refresh/", TokenRefreshView.as_view(), name='token_refresh'),
    path("token/verify/", TokenVerifyView.as_view(), name='token_verify'),
]