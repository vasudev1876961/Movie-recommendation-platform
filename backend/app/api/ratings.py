# backend/app/api/ratings.py
from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from backend.app.database.database import get_db
from backend.app.models.user import User
from backend.app.models.movie import Movie
from backend.app.models.rating import Rating
from backend.app.core.security import require_current_user, get_current_user

router = APIRouter(prefix="/api/movies", tags=["Ratings & Reviews"])

class RatingSubmission(BaseModel):
    score: float = Field(..., ge=1.0, le=10.0, description="Rating score (1-10 or 1-5 stars * 2)")
    review: Optional[str] = ""

class RatingResponse(BaseModel):
    movie_id: int
    user_score: Optional[float] = None
    user_review: Optional[str] = ""
    average_score: float
    total_ratings: int

@router.post("/{movie_id}/rate")
def rate_movie(
    movie_id: int,
    data: RatingSubmission,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    movie = db.query(Movie).filter(or_(Movie.id == movie_id, Movie.tmdb_id == movie_id)).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found.")

    rating = db.query(Rating).filter(
        Rating.user_id == user.id,
        Rating.movie_id == movie.id
    ).first()

    if rating:
        rating.score = data.score
        rating.review = data.review or ""
    else:
        rating = Rating(
            user_id=user.id,
            movie_id=movie.id,
            score=data.score,
            review=data.review or ""
        )
        db.add(rating)

    db.commit()
    return {"success": True, "message": f"Rating of {data.score} submitted for '{movie.title}'."}

@router.get("/{movie_id}/rating", response_model=RatingResponse)
def get_movie_rating_stats(
    movie_id: int,
    user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    movie = db.query(Movie).filter(or_(Movie.id == movie_id, Movie.tmdb_id == movie_id)).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found.")

    # Calculate average
    stats = db.query(
        func.avg(Rating.score).label("avg"),
        func.count(Rating.id).label("count")
    ).filter(Rating.movie_id == movie.id).first()

    user_rating = None
    if user:
        user_rating = db.query(Rating).filter(
            Rating.user_id == user.id,
            Rating.movie_id == movie.id
        ).first()

    avg = round(float(stats.avg), 1) if stats and stats.avg else movie.rating
    count = stats.count if stats else 0

    return RatingResponse(
        movie_id=movie.id,
        user_score=user_rating.score if user_rating else None,
        user_review=user_rating.review if user_rating else "",
        average_score=avg,
        total_ratings=count
    )
