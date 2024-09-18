# weather_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.weather_view, name='weather_view'),
]
