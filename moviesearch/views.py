import os
import pandas as pd
from fuzzywuzzy import process
from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView

# Construct dataset path using BASE_DIR
CSV_PATH = os.path.join(settings.BASE_DIR, "dataset", "tmdb_5000_movies.csv")

# Load the dataset
df = pd.read_csv(CSV_PATH)

class MovieSearchView(APIView):
    def get(self, request):
        query = request.GET.get("query", "").strip()
        if not query:
            return Response({"error": "Query string is required"}, status=400)

        # Find multiple best matches
        titles = df["original_title"].dropna().tolist()
        matches = process.extract(query, titles, limit=5) if titles else []

        if matches:
            results = [{"title": title, "confidence": score} for title, score in matches if score > 50]
            return Response({"matches": results})

        return Response({"error": "No close matches found"}, status=404)
