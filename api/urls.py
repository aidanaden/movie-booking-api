from django.urls import path
from .views import movieApi, movieDetailApi

app_name = 'api'

urlpatterns = [
    path('', movieApi, name='movieApi'),
    path('^/(?P<id>.+)/$', movieDetailApi, name='movieDetailApi' )
]