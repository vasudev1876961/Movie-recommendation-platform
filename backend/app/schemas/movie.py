# backend/app/schemas/movie.py
from typing import List, Optional
from pydantic import BaseModel

class GenreResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class CastResponse(BaseModel):
    id: int
    name: str
    character: Optional[str] = ""
    cast_order: Optional[int] = 0

    class Config:
        from_attributes = True

class DirectorResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class MovieListItem(BaseModel):
    id: int
    tmdb_id: int
    title: str
    rating: float
    release_date: Optional[str] = ""
    poster_path: Optional[str] = ""
    backdrop_path: Optional[str] = ""
    popularity: Optional[float] = 0.0
    trailer: Optional[str] = ""
    genres: List[str] = []

    class Config:
        from_attributes = True

class MovieDetails(BaseModel):
    id: int
    tmdb_id: int
    title: str
    overview: Optional[str] = ""
    release_date: Optional[str] = ""
    runtime: Optional[int] = 0
    rating: float
    vote_count: Optional[int] = 0
    popularity: Optional[float] = 0.0
    original_language: Optional[str] = "en"
    poster_path: Optional[str] = ""
    backdrop_path: Optional[str] = ""
    homepage: Optional[str] = ""
    tagline: Optional[str] = ""
    keywords: Optional[str] = ""
    trailer: Optional[str] = ""
    genres: List[GenreResponse] = []
    cast: List[CastResponse] = []
    directors: List[DirectorResponse] = []

    class Config:
        from_attributes = True

class PaginationResponse(BaseModel):
    total: int
    page: int
    pages: int
    limit: int
    movies: List[MovieListItem]
