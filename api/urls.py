from django.urls import path
from .views import movieApi

app_name = 'api'

urlpatterns = [
    path('', movieApi, name='movieApi')
]