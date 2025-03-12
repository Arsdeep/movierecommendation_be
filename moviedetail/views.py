from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
import requests

# Fetch movie details from OMDb API
def get_movie_details(title):
    url = "http://www.omdbapi.com/"
    params = {"t": title, "apikey": "7ed79aec"}  # Replace with actual API key
    response = requests.get(url, params=params)
    data = response.json()
    return data if response.status_code == 200 and data.get("Response") == "True" else {"error": data.get("Error", "Unable to fetch data.")}

# Django REST Framework API view class
class MovieDetailsView(APIView):
    def get(self, request):
        title = request.GET.get("title")
        if not title:
            return Response({"error": "Movie title is required."}, status=400)
        data = get_movie_details(title)
        return Response(data)
