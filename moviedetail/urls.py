from django.urls import path
from .views import MovieDetailsView

urlpatterns = [
    path("movie/", MovieDetailsView.as_view(), name="movie-details"),
] 
