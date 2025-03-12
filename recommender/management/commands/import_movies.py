from django.core.management.base import BaseCommand
import pandas as pd
import os
from django.conf import settings
from recommender.models import Movie
from datetime import datetime

class Command(BaseCommand):
    help = 'Import movies from TMDB dataset'

    def handle(self, *args, **options):
        movies_path = os.path.join(settings.BASE_DIR, 'dataset', 'tmdb_5000_movies.csv')
        
        if not os.path.exists(movies_path):
            self.stdout.write(self.style.ERROR(f'File not found: {movies_path}'))
            return
        
        try:
            # Load the dataset and print columns for debugging
            movies_df = pd.read_csv(movies_path)
            self.stdout.write(self.style.SUCCESS(f'Dataset columns: {list(movies_df.columns)}'))
            
            counter = 0
            
            for _, row in movies_df.iterrows():
                # Convert release date if available
                release_date = None
                if 'release_date' in movies_df.columns and pd.notna(row['release_date']):
                    try:
                        release_date = datetime.strptime(row['release_date'], '%Y-%m-%d').date()
                    except:
                        pass
                
                # Create defaults dict based on available columns
                defaults = {
                    'overview': row['overview'] if 'overview' in movies_df.columns and pd.notna(row['overview']) else '',
                    'vote_average': row['vote_average'] if 'vote_average' in movies_df.columns and pd.notna(row['vote_average']) else 0,
                    'vote_count': row['vote_count'] if 'vote_count' in movies_df.columns and pd.notna(row['vote_count']) else 0,
                }
                
                # Add release_date if we were able to parse it
                if release_date:
                    defaults['release_date'] = release_date
                
                # Add poster_path only if that column exists
                if 'poster_path' in movies_df.columns:
                    defaults['poster_path'] = row['poster_path'] if pd.notna(row['poster_path']) else ''
                
                # Update or create the movie
                movie, created = Movie.objects.update_or_create(
                    title=row['title'],
                    defaults=defaults
                )
                
                if created:
                    counter += 1
            
            self.stdout.write(self.style.SUCCESS(f'Successfully imported {counter} new movies'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error importing movies: {str(e)}'))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))