# recommender/recommendation_engine.py

import pandas as pd
import numpy as np
from ast import literal_eval
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os
import logging
import ast

def safe_literal_eval(x):
    try:
        return ast.literal_eval(x) if isinstance(x, str) else x
    except (ValueError, SyntaxError):
        return x  # Return original value if parsing fails


# Set up logging
logger = logging.getLogger(__name__)

class MovieRecommender:
    def __init__(self):
        self.df = None
        self.indices = None
        self.lowercase_indices = None  # New lowercase index
        self.cosine_sim = None
        self.initialized = False
        
    def initialize(self, credits_path, movies_path):
        """Initialize the recommendation engine with the dataset"""
        try:
            # Load data
            logger.info(f"Loading data from {credits_path} and {movies_path}")
            df1 = pd.read_csv(credits_path)  # credits dataset
            df2 = pd.read_csv(movies_path)   # movies dataset
            
            # Print columns for debugging
            logger.info(f"Credits columns: {list(df1.columns)}")
            logger.info(f"Movies columns: {list(df2.columns)}")
            
            # Based on the provided column names
            # df1 has: 'movie_id', 'title', 'cast', 'crew'
            # df2 has: 'id', 'title', and many other columns including 'keywords', 'genres'
            
            # Fix column name for merging - rename 'movie_id' to 'id' in df1
            if 'movie_id' in df1.columns and 'id' in df2.columns:
                df1 = df1.rename(columns={'movie_id': 'id'})
                logger.info("Renamed 'movie_id' to 'id' for merging")
            
            # Merge datasets on 'id'
            self.df = df2.merge(df1, on='id')
            
            # If the merge resulted in duplicate columns (like title_x and title_y), handle them
            if 'title_x' in self.df.columns and 'title_y' in self.df.columns:
                # Use title from movies dataset (df2)
                self.df['title'] = self.df['title_x']
                self.df = self.df.drop(['title_x', 'title_y'], axis=1)
                logger.info("Handled duplicate title columns after merge")
            
            # Make sure we have a 'title' column
            if 'title' not in self.df.columns:
                raise ValueError("No 'title' column found after merge")
            
            logger.info(f"Merged dataframe columns: {list(self.df.columns)}")
            logger.info(f"Merged dataframe shape: {self.df.shape}")
            
            # Parse string features to Python objects
            features = ['cast', 'crew', 'keywords', 'genres']
            for feature in features:
                if feature in self.df.columns:
                    # self.df[feature] = self.df[feature].apply(lambda x: literal_eval(x) if isinstance(x, str) else x) # for older version
                    self.df[feature] = self.df[feature].apply(safe_literal_eval)
            
            # Extract director
            if 'crew' in self.df.columns:
                self.df['director'] = self.df['crew'].apply(self._get_director)
            else:
                self.df['director'] = np.nan
            
            # Extract top 3 elements for features if they exist
            for feature in ['cast', 'keywords', 'genres']:
                if feature in self.df.columns:
                    self.df[feature] = self.df[feature].apply(self._get_list)
                else:
                    self.df[feature] = self.df.apply(lambda x: [], axis=1)
            
            # Clean data
            features = ['cast', 'keywords', 'genres', 'director']
            for feature in features:
                self.df[feature] = self.df[feature].apply(self._clean_data)
            
            # Create soup
            self.df['soup'] = self.df.apply(self._create_soup, axis=1)
            
            # Compute cosine similarity
            count = CountVectorizer(stop_words='english')
            count_matrix = count.fit_transform(self.df['soup'])
            self.cosine_sim = cosine_similarity(count_matrix, count_matrix)
            
            # Create reverse mapping for original titles and lowercase titles
            self.indices = pd.Series(self.df.index, index=self.df['title']).drop_duplicates()
            # Create lowercase title indices for case-insensitive lookup
            self.lowercase_indices = pd.Series(self.df.index, index=self.df['title'].str.lower()).drop_duplicates()

            self.initialized = True
            logger.info("Recommendation engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing recommendation engine: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise
        
    def _get_director(self, crew):
        """Extract director name from crew"""
        if not isinstance(crew, list):
            return np.nan
            
        for member in crew:
            if isinstance(member, dict) and 'job' in member and member['job'] == 'Director':
                return member['name']
        return np.nan
    
    def _get_list(self, x):
        """Get top 3 elements from list"""
        if isinstance(x, list):
            try:
                names = [i['name'] for i in x if isinstance(i, dict) and 'name' in i]
                if len(names) > 3:
                    names = names[:3]
                return names
            except (TypeError, KeyError):
                return []
        return []
    
    def _clean_data(self, x):
        """Clean data by converting to lowercase and removing spaces"""
        if isinstance(x, list):
            return [str.lower(i.replace(" ", "")) for i in x if isinstance(i, str)]
        else:
            if isinstance(x, str):
                return str.lower(x.replace(" ", ""))
            else:
                return ''
    
    def _create_soup(self, x):
        """Create text soup for vectorization"""
        keywords = ' '.join(x['keywords']) if 'keywords' in x else ''
        cast = ' '.join(x['cast']) if 'cast' in x else ''
        director = ' '.join([x['director']]) if 'director' in x and x['director'] else ''
        genres = ' '.join(x['genres']) if 'genres' in x else ''
        
        return ' '.join(filter(None, [keywords, cast, director, genres]))
    
    def get_recommendations(self, title, top_n=10):
        """Get movie recommendations based on title"""
        if not self.initialized:
            return []
        
        # Normalize input title: lowercase and strip whitespace
        normalized_title = title.strip().lower()
        
        # Check if the normalized title exists in lowercase indices
        if normalized_title not in self.lowercase_indices:
            logger.warning(f"Movie title '{title}' (normalized: '{normalized_title}') not found in indices")
            available_titles = list(self.indices.index)[:20]  # Show original titles
            logger.info(f"Some available titles: {available_titles}")
            return []
        
        # Get the index from the lowercase mapping
        idx = self.lowercase_indices[normalized_title]
        
        # Get similarity scores
        sim_scores = list(enumerate(self.cosine_sim[idx]))
        
        # Sort movies based on similarity scores
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        
        # Get top N most similar movies
        sim_scores = sim_scores[1:top_n+1]
        
        # Get movie indices
        movie_indices = [i[0] for i in sim_scores]
        
        # Return recommended movies with similarity scores
        recommendations = []
        for idx, i in enumerate(movie_indices):
            if i < len(self.df):  # Make sure index is valid
                recommendations.append({
                    'title': self.df['title'].iloc[i],
                    'similarity_score': float(sim_scores[idx][1])  # Convert numpy float to Python float
                })
        
        return recommendations