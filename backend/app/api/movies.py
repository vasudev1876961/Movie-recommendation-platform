# backend/app/api/movies.py
import math
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, or_
from backend.app.database.database import get_db
from backend.app.models.movie import Movie, Genre, CastMember, Director, MovieCast
from backend.app.schemas.movie import (
    MovieListItem,
    MovieDetails,
    GenreResponse,
    CastResponse,
    DirectorResponse,
    PaginationResponse
)

router = APIRouter(prefix="/api", tags=["Movies & Catalog"])

def format_movie_list_item(movie: Movie) -> MovieListItem:
    return MovieListItem(
        id=movie.id,
        tmdb_id=movie.tmdb_id,
        title=movie.title,
        rating=movie.rating,
        release_date=movie.release_date or "",
        poster_path=movie.poster_path or "",
        backdrop_path=movie.backdrop_path or "",
        popularity=movie.popularity or 0.0,
        trailer=getattr(movie, 'trailer', '') or "",
        genres=[g.name for g in movie.genres]
    )

def format_movie_details(movie: Movie) -> MovieDetails:
    cast_list = []
    for assoc in sorted(movie.cast_associations, key=lambda x: x.cast_order):
        cast_list.append(CastResponse(
            id=assoc.cast_member.id,
            name=assoc.cast_member.name,
            character=assoc.character or "",
            cast_order=assoc.cast_order
        ))

    return MovieDetails(
        id=movie.id,
        tmdb_id=movie.tmdb_id,
        title=movie.title,
        overview=movie.overview or "",
        release_date=movie.release_date or "",
        runtime=movie.runtime or 0,
        rating=movie.rating,
        vote_count=movie.vote_count or 0,
        popularity=movie.popularity or 0.0,
        original_language=movie.original_language or "en",
        poster_path=movie.poster_path or "",
        backdrop_path=movie.backdrop_path or "",
        homepage=movie.homepage or "",
        tagline=movie.tagline or "",
        keywords=movie.keywords or "",
        trailer=getattr(movie, 'trailer', '') or "",
        genres=[GenreResponse(id=g.id, name=g.name) for g in movie.genres],
        cast=cast_list,
        directors=[DirectorResponse(id=d.id, name=d.name) for d in movie.directors]
    )

@router.get("/movies", response_model=PaginationResponse)
def get_movies(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(24, ge=1, le=100, description="Items per page"),
    genre: Optional[str] = Query(None, description="Filter by genre name"),
    year: Optional[int] = Query(None, description="Filter by release year"),
    min_rating: Optional[float] = Query(None, ge=0.0, le=10.0, description="Minimum rating"),
    sort_by: Optional[str] = Query("popularity", description="Sort field: popularity, rating, release_date, title"),
    order: Optional[str] = Query("desc", description="Sort order: asc, desc"),
    search: Optional[str] = Query(None, description="Search query across title, overview, keywords"),
    db: Session = Depends(get_db)
):
    query = db.query(Movie)

    # 1. Search filter
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Movie.title.ilike(term),
                Movie.overview.ilike(term),
                Movie.keywords.ilike(term)
            )
        )

    # 2. Genre filter
    if genre and genre.strip() and genre.lower() != "all":
        query = query.filter(Movie.genres.any(Genre.name.ilike(genre.strip())))

    # 3. Year filter
    if year:
        query = query.filter(Movie.release_date.like(f"{year}%"))

    # 4. Rating filter
    if min_rating is not None:
        query = query.filter(Movie.rating >= min_rating)

    # Total count after filters
    total = query.count()

    # 5. Sorting
    sort_column = Movie.popularity
    if sort_by == "rating":
        sort_column = Movie.rating
    elif sort_by == "release_date":
        sort_column = Movie.release_date
    elif sort_by == "title":
        sort_column = Movie.title

    if order.lower() == "asc":
        query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc(sort_column))

    # 6. Pagination
    offset = (page - 1) * limit
    movies = query.offset(offset).limit(limit).all()
    pages = math.ceil(total / limit) if limit > 0 else 1

    return PaginationResponse(
        total=total,
        page=page,
        pages=pages,
        limit=limit,
        movies=[format_movie_list_item(m) for m in movies]
    )

@router.get("/movies/popular", response_model=List[MovieListItem])
def get_popular_movies(
    limit: int = Query(20, ge=1, le=50),
    exclude_ids: Optional[str] = Query("", description="Comma-separated movie IDs to exclude"),
    db: Session = Depends(get_db)
):
    query = db.query(Movie)
    if exclude_ids:
        ids = [int(x) for x in exclude_ids.split(",") if x.strip().isdigit()]
        if ids:
            query = query.filter(Movie.id.notin_(ids))
    movies = query.order_by(desc(Movie.popularity)).limit(limit).all()
    return [format_movie_list_item(m) for m in movies]

@router.get("/movies/top-rated", response_model=List[MovieListItem])
def get_top_rated_movies(
    limit: int = Query(20, ge=1, le=50),
    exclude_ids: Optional[str] = Query("", description="Comma-separated movie IDs to exclude"),
    db: Session = Depends(get_db)
):
    query = db.query(Movie)
    if exclude_ids:
        ids = [int(x) for x in exclude_ids.split(",") if x.strip().isdigit()]
        if ids:
            query = query.filter(Movie.id.notin_(ids))
    movies = query.order_by(desc(Movie.rating)).limit(limit).all()
    return [format_movie_list_item(m) for m in movies]

@router.get("/movies/trending", response_model=List[MovieListItem])
def get_trending_movies(
    limit: int = Query(20, ge=1, le=50),
    exclude_ids: Optional[str] = Query("", description="Comma-separated movie IDs to exclude"),
    db: Session = Depends(get_db)
):
    query = db.query(Movie)
    if exclude_ids:
        ids = [int(x) for x in exclude_ids.split(",") if x.strip().isdigit()]
        if ids:
            query = query.filter(Movie.id.notin_(ids))
    movies = query.order_by(desc(Movie.popularity), desc(Movie.rating)).limit(limit).all()
    return [format_movie_list_item(m) for m in movies]

@router.get("/movies/hidden-gems", response_model=List[MovieListItem])
def get_hidden_gems_movies(
    limit: int = Query(20, ge=1, le=50),
    exclude_ids: Optional[str] = Query("", description="Comma-separated movie IDs to exclude"),
    db: Session = Depends(get_db)
):
    query = db.query(Movie).filter(Movie.rating >= 7.5)
    if exclude_ids:
        ids = [int(x) for x in exclude_ids.split(",") if x.strip().isdigit()]
        if ids:
            query = query.filter(Movie.id.notin_(ids))
    movies = query.order_by(desc(Movie.rating)).limit(limit).all()
    return [format_movie_list_item(m) for m in movies]

@router.get("/movies/by-mood/{mood}", response_model=List[MovieListItem])
def get_movies_by_mood(
    mood: str,
    limit: int = Query(15, ge=1, le=50),
    exclude_ids: Optional[str] = Query("", description="Comma-separated movie IDs to exclude"),
    db: Session = Depends(get_db)
):
    query = db.query(Movie).filter(Movie.mood.ilike(f"%{mood.strip()}%"))
    if exclude_ids:
        ids = [int(x) for x in exclude_ids.split(",") if x.strip().isdigit()]
        if ids:
            query = query.filter(Movie.id.notin_(ids))
    movies = query.order_by(desc(Movie.rating), desc(Movie.popularity)).limit(limit).all()
    return [format_movie_list_item(m) for m in movies]

@router.get("/movies/shelves/deduplicated")
def get_deduplicated_homepage_shelves(db: Session = Depends(get_db)):
    """Returns 0-duplicate categorized shelves for the homepage."""
    all_movies = db.query(Movie).all()
    used_ids = set()

    def pick_movies(filter_fn, sort_key, limit=10):
        candidates = [m for m in all_movies if m.id not in used_ids and filter_fn(m)]
        candidates.sort(key=sort_key, reverse=True)
        chosen = candidates[:limit]
        for m in chosen:
            used_ids.add(m.id)
        return [format_movie_list_item(m) for m in chosen]

    # 1. Featured Hero Blockbuster (Top 5 rotating candidates)
    hero_candidates = sorted(all_movies, key=lambda m: (m.popularity, m.rating), reverse=True)[:5]
    hero_items = [format_movie_list_item(m) for m in hero_candidates]
    # Mark top 1 hero as used so shelves don't immediately repeat it as card #1
    if hero_candidates:
        used_ids.add(hero_candidates[0].id)

    # 2. Shelf: Trending Blockbusters
    trending = pick_movies(lambda m: True, lambda m: (m.popularity, m.rating), limit=8)

    # 3. Shelf: All-Time Masterpieces (Rating >= 8.5)
    masterpieces = pick_movies(lambda m: m.rating >= 8.4, lambda m: (m.rating, m.popularity), limit=8)

    # 4. Shelf: Sci-Fi & Mind-Bending Thrillers
    scifi = pick_movies(
        lambda m: any(g.name in ["Science Fiction", "Mystery"] for g in m.genres) or "Mind-bending" in (m.mood or ""),
        lambda m: (m.rating, m.popularity),
        limit=8
    )

    # 5. Shelf: Action, Crime & Epic Sagas
    action = pick_movies(
        lambda m: any(g.name in ["Action", "Crime", "Adventure"] for g in m.genres),
        lambda m: (m.popularity, m.rating),
        limit=8
    )

    # 6. Shelf: Animation, Family & Feel-Good
    animation = pick_movies(
        lambda m: any(g.name in ["Animation", "Family", "Comedy"] for g in m.genres) or "Feel Good" in (m.mood or ""),
        lambda m: (m.rating, m.popularity),
        limit=8
    )

    # 7. Shelf: Dark & Psychological Thrillers
    dark_gems = pick_movies(
        lambda m: any(g.name in ["Horror", "Thriller", "Drama"] for g in m.genres) or "Dark" in (m.mood or ""),
        lambda m: (m.rating, m.popularity),
        limit=8
    )

    return {
        "hero_movies": hero_items,
        "shelves": [
            {"title": "Trending Blockbusters", "icon": "fas fa-fire", "movies": trending, "id": "trending-shelf"},
            {"title": "All-Time Masterpieces", "icon": "fas fa-trophy", "movies": masterpieces, "id": "masterpieces-shelf"},
            {"title": "Sci-Fi & Mind-Bending", "icon": "fas fa-brain", "movies": scifi, "id": "scifi-shelf"},
            {"title": "Action & Epic Sagas", "icon": "fas fa-shield-alt", "movies": action, "id": "action-shelf"},
            {"title": "Animation & Family Favorites", "icon": "fas fa-wand-magic-sparkles", "movies": animation, "id": "animation-shelf"},
            {"title": "Dark & Psychological Thrillers", "icon": "fas fa-mask", "movies": dark_gems, "id": "dark-shelf"}
        ]
    }

@router.get("/movies/search", response_model=List[MovieListItem])
def search_movies_endpoint(
    q: str = Query("", description="Search term"),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db)
):
    if not q.strip():
        return []
    term = f"%{q.strip()}%"
    movies = db.query(Movie).filter(
        or_(
            Movie.title.ilike(term),
            Movie.overview.ilike(term),
            Movie.keywords.ilike(term)
        )
    ).limit(limit).all()
    return [format_movie_list_item(m) for m in movies]

@router.get("/genres", response_model=List[GenreResponse])
def get_all_genres(db: Session = Depends(get_db)):
    genres = db.query(Genre).order_by(asc(Genre.name)).all()
    return [GenreResponse(id=g.id, name=g.name) for g in genres]

@router.get("/recommendations/personalized", response_model=List[MovieListItem])
def get_personalized_recommendations(limit: int = Query(12, ge=1, le=30), db: Session = Depends(get_db)):
    # Return high-rated popular mix
    movies = db.query(Movie).filter(Movie.rating >= 7.8).order_by(desc(Movie.popularity)).limit(limit).all()
    return [format_movie_list_item(m) for m in movies]

@router.post("/movies/recommendations/wizard", response_model=List[MovieListItem])
def get_wizard_recommendations(prefs: dict, db: Session = Depends(get_db)):
    genres_filter = prefs.get("genres", [])
    query = db.query(Movie)
    if genres_filter:
        query = query.filter(Movie.genres.any(Genre.name.in_(genres_filter)))
    movies = query.order_by(desc(Movie.rating), desc(Movie.popularity)).limit(12).all()
    if not movies:
        movies = db.query(Movie).order_by(desc(Movie.rating)).limit(12).all()
    return [format_movie_list_item(m) for m in movies]

@router.get("/movies/{movie_id}/recommendations", response_model=List[MovieListItem])
def get_movie_recommendations(movie_id: int, limit: int = Query(10, ge=1, le=20), db: Session = Depends(get_db)):
    source = db.query(Movie).filter(or_(Movie.id == movie_id, Movie.tmdb_id == movie_id)).first()
    if not source:
        return []
    genre_ids = [g.id for g in source.genres]
    similar = db.query(Movie).filter(
        Movie.id != source.id,
        Movie.genres.any(Genre.id.in_(genre_ids))
    ).order_by(desc(Movie.rating), desc(Movie.popularity)).limit(limit).all()
    return [format_movie_list_item(m) for m in similar]

@router.get("/movies/{movie_id}", response_model=MovieDetails)
def get_movie_by_id(movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(Movie).filter(or_(Movie.id == movie_id, Movie.tmdb_id == movie_id)).first()
    if not movie:
        raise HTTPException(status_code=404, detail=f"Movie with ID {movie_id} not found")
    return format_movie_details(movie)
