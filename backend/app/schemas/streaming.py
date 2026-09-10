# backend/app/schemas/streaming.py
from typing import List, Optional
from pydantic import BaseModel

class StreamingProviderInfo(BaseModel):
    provider_id: str
    name: str
    logo_url: Optional[str] = None
    brand_color: str = "#6366f1"
    display_priority: int = 0
    total_movies: Optional[int] = 0

    class Config:
        from_attributes = True

class WatchOption(BaseModel):
    provider: StreamingProviderInfo
    type: str  # "stream" (flatrate), "rent", "buy", "free"
    quality: str = "4K"  # "4K", "HD", "SD"
    price: Optional[str] = "Included"
    deep_link: str

    class Config:
        from_attributes = True

class MovieStreamingAvailability(BaseModel):
    movie_id: int
    tmdb_id: int
    title: str
    region: str = "US"
    stream: List[WatchOption] = []
    rent: List[WatchOption] = []
    buy: List[WatchOption] = []
    free: List[WatchOption] = []
    last_updated: str

    class Config:
        from_attributes = True

class ProvidersCatalogResponse(BaseModel):
    region: str
    total_providers: int
    providers: List[StreamingProviderInfo]

class StreamingBrowseResponse(BaseModel):
    provider: str
    region: str
    total: int
    page: int
    pages: int
    movies: List[dict]
