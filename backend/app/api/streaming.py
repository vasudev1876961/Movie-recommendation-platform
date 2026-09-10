# backend/app/api/streaming.py
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.app.database.database import get_db
from backend.app.schemas.streaming import (
    ProvidersCatalogResponse,
    MovieStreamingAvailability,
    StreamingBrowseResponse
)
from backend.app.services.streaming_resolver import streaming_resolver
from backend.app.api.movies import format_movie_list_item

router = APIRouter(prefix="/api/streaming", tags=["Phase 7: Streaming Providers Resolver"])

@router.get("/providers", response_model=ProvidersCatalogResponse)
def get_supported_providers(
    region: str = Query("US", description="Two-letter country code (US, GB, CA, IN)"),
    db: Session = Depends(get_db)
):
    """Returns list of supported streaming platforms with movie availability counts."""
    providers = streaming_resolver.list_all_providers(region=region, db=db)
    return ProvidersCatalogResponse(
        region=region.upper(),
        total_providers=len(providers),
        providers=providers
    )

@router.get("/movie/{movie_id}", response_model=MovieStreamingAvailability)
def get_movie_streaming_availability(
    movie_id: int,
    region: str = Query("US", description="Two-letter country code"),
    db: Session = Depends(get_db)
):
    """Retrieves real-time streaming, rental, and digital purchase availability for a movie."""
    avail = streaming_resolver.get_availability_by_id(movie_id=movie_id, db=db, region=region)
    if not avail:
        raise HTTPException(status_code=404, detail=f"Movie with ID {movie_id} not found")
    return avail

@router.get("/browse", response_model=StreamingBrowseResponse)
def browse_movies_by_provider(
    provider: str = Query(..., description="Provider identifier (e.g. 'netflix', 'prime', 'max', 'disney')"),
    region: str = Query("US", description="Two-letter country code"),
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Finds all movies in the catalog currently available on the specified streaming platform."""
    matched_movies = streaming_resolver.get_movies_by_provider(provider_id=provider, region=region, db=db)
    total = len(matched_movies)

    start = (page - 1) * limit
    end = start + limit
    page_movies = matched_movies[start:end]

    formatted = [format_movie_list_item(m).model_dump() for m in page_movies]
    pages = (total + limit - 1) // limit if total > 0 else 1

    return StreamingBrowseResponse(
        provider=provider.lower(),
        region=region.upper(),
        total=total,
        page=page,
        pages=pages,
        movies=formatted
    )
