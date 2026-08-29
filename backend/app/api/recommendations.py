# backend/app/api/recommendations.py
from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.app.database.database import get_db
from backend.app.models.user import User
from backend.app.models.movie import Movie
from backend.app.schemas.movie import MovieListItem
from backend.app.api.movies import format_movie_list_item
from backend.app.core.security import get_current_user, require_current_user
from backend.app.services.hybrid_recommender import hybrid_engine
from backend.app.services.tfidf_recommender import tfidf_engine
from backend.app.services.collaborative_recommender import collaborative_engine

router = APIRouter(prefix="/api/recommendations", tags=["Recommendation Engine (Phase 3 Hybrid)"])

class HybridRecommendationItem(BaseModel):
    movie: MovieListItem
    match_score: float
    reasoning: str
    hybrid_score: Optional[float] = 0.0
    content_score: Optional[float] = 0.0
    collab_score: Optional[float] = 0.0

class SimilarMovieItem(BaseModel):
    movie: MovieListItem
    match_score: float
    similarity: float
    reasoning: str

class WizardPreferenceRequest(BaseModel):
    genres: List[str] = Field(default_factory=list)
    mood: Optional[str] = ""
    era: Optional[str] = ""
    minRating: Optional[float] = None
    runtime: Optional[str] = ""

class WizardRecommendationItem(BaseModel):
    movie: MovieListItem
    score: int

@router.get("/hybrid", response_model=List[HybridRecommendationItem])
def get_hybrid_recommendations(
    limit: int = Query(12, ge=1, le=30),
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns personalized hybrid recommendations dynamically combining:
    - Scikit-Learn TF-IDF Content profile similarity
    - SVD Collaborative Filtering ratings prediction
    - Bayesian quality & popularity priors
    """
    user_id = current_user.id if current_user else None
    results = hybrid_engine.get_personalized_recommendations(
        user_id=user_id,
        db=db,
        limit=limit
    )

    formatted = []
    for item in results:
        formatted.append(HybridRecommendationItem(
            movie=format_movie_list_item(item["movie"]),
            match_score=item["match_score"],
            reasoning=item["reasoning"],
            hybrid_score=round(item.get("hybrid_score", 0.0), 3),
            content_score=round(item.get("content_score", 0.0), 3),
            collab_score=round(item.get("collab_score", 0.0), 3)
        ))
    return formatted

@router.get("/content/{movie_id}", response_model=List[SimilarMovieItem])
def get_content_recommendations_for_movie(
    movie_id: int,
    limit: int = Query(8, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """
    Returns top-N TF-IDF content recommendations for a single movie with match percentages and reasoning.
    """
    # Check if movie exists
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail=f"Movie with ID {movie_id} not found")

    results = hybrid_engine.get_content_recommendations_for_movie(
        movie_id=movie_id,
        db=db,
        limit=limit
    )

    return [
        SimilarMovieItem(
            movie=format_movie_list_item(item["movie"]),
            match_score=item["match_score"],
            similarity=item["similarity"],
            reasoning=item["reasoning"]
        )
        for item in results
    ]

@router.get("/collaborative", response_model=List[HybridRecommendationItem])
def get_collaborative_recommendations(
    limit: int = Query(12, ge=1, le=30),
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns pure Collaborative Filtering recommendations based on SVD matrix factorization.
    """
    if not collaborative_engine.is_trained:
        collaborative_engine.fit(db)

    recs = collaborative_engine.get_collaborative_recommendations(
        user_id=current_user.id,
        top_n=limit
    )

    if not recs:
        # Fallback to hybrid if user has sparse collaborative overlap
        return get_hybrid_recommendations(limit=limit, current_user=current_user, db=db)

    movie_ids = [m_id for m_id, _, _ in recs]
    movies = db.query(Movie).filter(Movie.id.in_(movie_ids)).all()
    movies_map = {m.id: m for m in movies}

    formatted = []
    for m_id, score, reason in recs:
        if m_id in movies_map:
            pct = min(99.0, max(75.0, round(score * 100.0, 1)))
            formatted.append(HybridRecommendationItem(
                movie=format_movie_list_item(movies_map[m_id]),
                match_score=pct,
                reasoning=reason,
                collab_score=round(score, 3)
            ))
    return formatted

@router.post("/wizard", response_model=List[WizardRecommendationItem])
def get_wizard_recommendations_endpoint(
    prefs: WizardPreferenceRequest,
    limit: int = Query(12, ge=1, le=24),
    db: Session = Depends(get_db)
):
    """
    Executes enhanced recommendation wizard query matching user constraints with TF-IDF features.
    """
    results = hybrid_engine.get_wizard_recommendations(
        genres=prefs.genres,
        mood=prefs.mood or "",
        era=prefs.era or "",
        min_rating=prefs.minRating,
        runtime=prefs.runtime or "",
        db=db,
        limit=limit
    )

    return [
        WizardRecommendationItem(
            movie=format_movie_list_item(item["movie"]),
            score=item["score"]
        )
        for item in results
    ]

@router.post("/retrain")
def retrain_models(db: Session = Depends(get_db)):
    """
    Forces retraining and caching of TF-IDF feature matrices and SVD collaborative models.
    """
    stats = hybrid_engine.retrain_all(db)
    return {
        "status": "success",
        "message": "Recommendation models retrained successfully.",
        "stats": stats
    }
