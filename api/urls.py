from django.urls import path
# from .views import movieApi, movieDetailApi
from .views import MovieListAPIView

app_name = 'api'

urlpatterns = [
    path('', MovieListAPIView.as_view(), name='movie_list'),
    # path(r'^/(?P<id>[\w-]+)/$', MovieListAPIView.as_view(), name='movie_detail')
]