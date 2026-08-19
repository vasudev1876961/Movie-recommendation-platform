# backend/app/api/watchlist.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from backend.app.database.database import get_db
from backend.app.models.user import User, WatchlistItem
from backend.app.models.movie import Movie
from backend.app.schemas.movie import MovieListItem
from backend.app.api.movies import format_movie_list_item
from backend.app.core.security import require_current_user, get_current_user

router = APIRouter(prefix="/api/watchlist", tags=["Watchlist"])

@router.get("", response_model=List[MovieListItem])
def get_user_watchlist(
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    items = db.query(WatchlistItem).filter(WatchlistItem.user_id == user.id).all()
    movie_ids = [item.movie_id for item in items]
    movies = db.query(Movie).filter(Movie.id.in_(movie_ids)).all()
    return [format_movie_list_item(m) for m in movies]

@router.post("/{movie_id}")
def toggle_watchlist_item(
    movie_id: int,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    # Find movie by ID or tmdb_id
    movie = db.query(Movie).filter(or_(Movie.id == movie_id, Movie.tmdb_id == movie_id)).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found.")

    existing = db.query(WatchlistItem).filter(
        WatchlistItem.user_id == user.id,
        WatchlistItem.movie_id == movie.id
    ).first()

    if existing:
        db.delete(existing)
        db.commit()
        return {"saved": False, "message": f"Removed '{movie.title}' from watchlist."}
    else:
        new_item = WatchlistItem(user_id=user.id, movie_id=movie.id)
        db.add(new_item)
        db.commit()
        return {"saved": True, "message": f"Added '{movie.title}' to watchlist."}

@router.delete("/{movie_id}")
def remove_watchlist_item(
    movie_id: int,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db)
):
    movie = db.query(Movie).filter(or_(Movie.id == movie_id, Movie.tmdb_id == movie_id)).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found.")

    existing = db.query(WatchlistItem).filter(
        WatchlistItem.user_id == user.id,
        WatchlistItem.movie_id == movie.id
    ).first()

    if existing:
        db.delete(existing)
        db.commit()
        return {"success": True, "message": "Movie removed from watchlist."}
    return {"success": False, "message": "Movie was not in watchlist."}
