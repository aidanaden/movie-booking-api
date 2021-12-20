from django.urls import path
# from .views import movieApi, movieDetailApi
from .views import MovieListAPIView
from .views import MovieDetailAPIView

app_name = 'api'

urlpatterns = [
    path('', MovieListAPIView.as_view(), name='movie_list'),
    path(r'^/(?P<pk>[\w-]+)/$', MovieDetailAPIView.as_view(), name='movie_detail')
]