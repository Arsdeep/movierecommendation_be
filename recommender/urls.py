from django.urls import path
from .views import RecommendMovies

urlpatterns = [
    path('recommend/', RecommendMovies.as_view(), name='recommend-movies'),
]