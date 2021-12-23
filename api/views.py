
from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse

from .models import Movie
from .serializers import MovieSerializer

from rest_framework.generics import ListAPIView
from rest_framework.generics import RetrieveAPIView

class MovieListAPIView(ListAPIView):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

class MovieDetailAPIView(RetrieveAPIView):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
    lookup_field = 'slug'