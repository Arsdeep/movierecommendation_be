# recommender/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import os
import logging
import difflib

from .recommendation_engine import MovieRecommender
from .serializers import MovieRecommendationSerializer

# Set up logging
logger = logging.getLogger(__name__)

# Initialize recommender engine
recommender = MovieRecommender()

class RecommendMovies(APIView):
    def get(self, request, format=None):
        # Get movie title from query parameters
        movie_title = request.query_params.get('title', None)
        
        if not movie_title:
            return Response(
                {"error": "Please provide a movie title"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Initialize the engine if not already initialized
        if not recommender.initialized:
            credits_path = os.path.join(settings.BASE_DIR, 'dataset', 'tmdb_5000_credits.csv')
            movies_path = os.path.join(settings.BASE_DIR, 'dataset', 'tmdb_5000_movies.csv')
            
            # Check if files exist
            if not os.path.exists(credits_path):
                logger.error(f"Credits file not found: {credits_path}")
                return Response(
                    {"error": f"Credits dataset file not found at {credits_path}"}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
            if not os.path.exists(movies_path):
                logger.error(f"Movies file not found: {movies_path}")
                return Response(
                    {"error": f"Movies dataset file not found at {movies_path}"}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            try:
                logger.info("Initializing recommendation engine")
                recommender.initialize(credits_path, movies_path)
            except Exception as e:
                logger.error(f"Failed to initialize recommendation engine: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                return Response(
                    {"error": f"Failed to initialize recommendation engine: {str(e)}"}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        # Get recommendations
        try:
            recommendations = recommender.get_recommendations(movie_title)
            
            if not recommendations:
                # If we have indices, try to find similar movie titles
                if hasattr(recommender, 'indices') and recommender.indices is not None:
                    available_titles = list(recommender.indices.index)
                    
                    # Find closest matches using difflib
                    closest_matches = difflib.get_close_matches(
                        movie_title, available_titles, n=5, cutoff=0.6
                    )
                    
                    if closest_matches:
                        return Response({
                            "error": f"Movie '{movie_title}' not found in the dataset",
                            "suggestions": closest_matches
                        }, status=status.HTTP_404_NOT_FOUND)
                    else:
                        # Sample some random titles if no close matches
                        import random
                        random_titles = random.sample(available_titles, min(5, len(available_titles)))
                        return Response({
                            "error": f"Movie '{movie_title}' not found in the dataset",
                            "available_sample": random_titles,
                            "tip": "Try one of these sample titles or make sure to use the exact movie title"
                        }, status=status.HTTP_404_NOT_FOUND)
                else:
                    return Response({
                        "error": f"Movie '{movie_title}' not found in the dataset or no recommendations available"
                    }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return Response(
                {"error": f"Error getting recommendations: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Serialize and return
        serializer = MovieRecommendationSerializer(recommendations, many=True)
        return Response(serializer.data)