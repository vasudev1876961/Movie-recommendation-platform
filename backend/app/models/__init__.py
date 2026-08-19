# backend/app/models/__init__.py
from .movie import Movie, Genre, CastMember, Director, MovieCast, movie_genre, movie_director
from .user import User, WatchlistItem, WatchHistory, UserPreference
from .rating import Rating
