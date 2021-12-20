
from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse

from .models import Movie
from .serializers import MovieSerializer

from rest_framework.generics import ListAPIView

# Create your views here.
# @csrf_exempt
# def movieApi(request):
#     if request.method == 'GET':
#         movies = Movie.objects.all()
#         movies_serializer = MovieSerializer(movies, many=True)
#         return JsonResponse(movies_serializer.data, safe=False)

# @csrf_exempt
# def movieDetailApi(request):
#     if request.method == 'GET':
#         id = request.query_params['id']
#         movie = Movie.objects.all(id=id)
#         movie_serializer = MovieSerializer(movie, many=False)
#         return JsonResponse(movie_serializer.data, safe=False)
        
        

class MovieListAPIView(ListAPIView):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

# class MovieDetail(generics.RetrieveDestroyAPIView):
#     pass