from django.urls import path
from .views import RecommendMovies

urlpatterns = [
    path("", RecommendMovies.as_view(), name='recommend-movies'),
]