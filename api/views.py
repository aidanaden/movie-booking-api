import json
from django.shortcuts import render
from django.views.decorators import csrf
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics
from rest_framework.parsers import JSONParser
from django.http.response import JsonResponse

from .models import Movie
from .serializers import MovieSerializer

# Create your views here.
@csrf_exempt
def movieApi(request):
    if request.method == 'GET':
        movies = Movie.objects.all()
        movies_serializer = MovieSerializer(movies, many=True)
        return JsonResponse(movies_serializer.data, safe=False)

@csrf_exempt
def movieDetailApi(request):
    if request.method == 'GET':
        id = request.query_params['id']
        movie = Movie.objects.all(id=id)
        movie_serializer = MovieSerializer(movie, many=False)
        return JsonResponse(movie_serializer.data, safe=False)
        
        

# class MovieList(generics.ListCreateAPIView):
#     queryset = Movie.objects.all()
#     serializer_class = MovieSerializer

# class MovieDetail(generics.RetrieveDestroyAPIView):
#     pass