# backend/app/api/semantic.py
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.app.database.database import get_db
from backend.app.models.movie import Movie
from backend.app.schemas.movie import MovieListItem
from backend.app.api.movies import format_movie_list_item
from backend.app.services.semantic_search import semantic_search_engine

router = APIRouter(prefix="/api", tags=["Semantic Vector Search"])

class SemanticSearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 12
    min_score: Optional[float] = 0.15
    genre: Optional[str] = None

class SemanticSearchResultItem(BaseModel):
    movie: MovieListItem
    cosine_similarity: float
    match_score: float
    reasoning: str
    thematic_tags: List[str]

class SemanticSearchResponse(BaseModel):
    query: str
    total: int
    results: List[SemanticSearchResultItem]

@router.post("/search/semantic", response_model=SemanticSearchResponse)
def search_semantic(payload: SemanticSearchRequest, db: Session = Depends(get_db)):
    """
    Executes a deep neural semantic search over the movie catalog
    using SentenceTransformers dense vector embeddings and cosine similarity.
    """
    if not payload.query or not payload.query.strip():
        return SemanticSearchResponse(query="", total=0, results=[])

    if not semantic_search_engine.is_trained:
        semantic_search_engine.fit(db)

    raw_results = semantic_search_engine.search(
        query=payload.query.strip(),
        top_k=payload.limit or 12,
        min_score=payload.min_score or 0.15,
        genre_filter=payload.genre
    )

    if not raw_results:
        return SemanticSearchResponse(query=payload.query, total=0, results=[])

    # Fetch movie models for the matched IDs
    movie_ids = [r["movie_id"] for r in raw_results]
    movies = db.query(Movie).filter(Movie.id.in_(movie_ids)).all()
    movie_map = {m.id: m for m in movies}

    formatted_results = []
    for r in raw_results:
        m = movie_map.get(r["movie_id"])
        if m:
            formatted_results.append(SemanticSearchResultItem(
                movie=format_movie_list_item(m),
                cosine_similarity=r["cosine_similarity"],
                match_score=r["match_score"],
                reasoning=r["reasoning"],
                thematic_tags=r.get("thematic_tags", [])
            ))

    return SemanticSearchResponse(
        query=payload.query,
        total=len(formatted_results),
        results=formatted_results
    )

@router.get("/movies/{movie_id}/semantic-similar", response_model=List[SemanticSearchResultItem])
def get_semantic_twins(
    movie_id: int,
    limit: int = Query(6, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """
    Discovers conceptual and thematic twin movies using nearest neighbors in dense embedding space.
    """
    if not semantic_search_engine.is_trained:
        semantic_search_engine.fit(db)

    # Find movie
    source = db.query(Movie).filter(Movie.id == movie_id).first()
    if not source:
        raise HTTPException(status_code=404, detail=f"Movie with ID {movie_id} not found")

    twins = semantic_search_engine.get_conceptual_twins(source.id, top_n=limit)
    if not twins:
        return []

    twin_ids = [m_id for m_id, _, _ in twins]
    twin_movies = db.query(Movie).filter(Movie.id.in_(twin_ids)).all()
    twin_map = {m.id: m for m in twin_movies}

    results = []
    for m_id, score, reason in twins:
        m = twin_map.get(m_id)
        if m:
            match_pct = min(99.0, max(65.0, round(50.0 + (score * 60.0), 1)))
            results.append(SemanticSearchResultItem(
                movie=format_movie_list_item(m),
                cosine_similarity=round(score, 4),
                match_score=match_pct,
                reasoning=reason,
                thematic_tags=[g.name for g in m.genres]
            ))

    return results

@router.post("/admin/embeddings/reindex")
def reindex_embeddings(db: Session = Depends(get_db)):
    """Forces recomputation and disk-caching of all movie neural vector embeddings."""
    success = semantic_search_engine.fit(db, force_recompute=True)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to reindex vector embeddings")
    return {
        "status": "success",
        "message": f"Successfully reindexed {len(semantic_search_engine.movie_ids)} movie vector embeddings.",
        "embedding_dimensions": int(semantic_search_engine.embedding_matrix.shape[1]) if semantic_search_engine.embedding_matrix is not None else 0
    }
