# backend/app/database/seed.py
import os
import json
import time
import logging
import httpx
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from backend.app.database.database import engine, SessionLocal, Base
from backend.app.models.movie import Movie, Genre, CastMember, Director, MovieCast

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seeder")

TMDB_API_KEY = os.getenv("TMDB_API_KEY", "").strip()
TMDB_BASE_URL = "https://api.themoviedb.org/3"

GENRE_MAP = {
    28: "Action",
    12: "Adventure",
    16: "Animation",
    35: "Comedy",
    80: "Crime",
    99: "Documentary",
    18: "Drama",
    10751: "Family",
    14: "Fantasy",
    36: "History",
    27: "Horror",
    10402: "Music",
    9648: "Mystery",
    10749: "Romance",
    878: "Science Fiction",
    10770: "TV Movie",
    53: "Thriller",
    10752: "War",
    37: "Western"
}

def init_db():
    logger.info("Initializing SQLite database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully.")

def get_or_create_genre(db: Session, name: str) -> Genre:
    genre = db.query(Genre).filter(Genre.name == name).first()
    if not genre:
        genre = Genre(name=name)
        db.add(genre)
        db.flush()
    return genre

def get_or_create_director(db: Session, name: str) -> Director:
    director = db.query(Director).filter(Director.name == name).first()
    if not director:
        director = Director(name=name)
        db.add(director)
        db.flush()
    return director

def get_or_create_cast_member(db: Session, name: str) -> CastMember:
    cast_member = db.query(CastMember).filter(CastMember.name == name).first()
    if not cast_member:
        cast_member = CastMember(name=name)
        db.add(cast_member)
        db.flush()
    return cast_member

def fetch_tmdb(client: httpx.Client, endpoint: str, params: dict = {}) -> dict:
    url = f"{TMDB_BASE_URL}{endpoint}"
    p = {"api_key": TMDB_API_KEY, **params}
    try:
        response = client.get(url, params=p, timeout=15.0)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 2))
            logger.warning(f"Rate limited by TMDB. Sleeping for {retry_after}s...")
            time.sleep(retry_after)
            return fetch_tmdb(client, endpoint, params)
        else:
            logger.warning(f"TMDB request failed for {endpoint} status={response.status_code}")
            return {}
    except Exception as e:
        logger.error(f"Error fetching from TMDB: {e}")
        return {}

def collect_movie_ids(client: httpx.Client, target_count: int = 1200) -> list[int]:
    """Collects unique movie IDs across multiple discovery criteria."""
    unique_ids = set()
    logger.info(f"Gathering movie IDs from multiple TMDB endpoints (target: {target_count}+)...")

    # 1. Popular (Pages 1 to 10)
    for page in range(1, 11):
        data = fetch_tmdb(client, "/movie/popular", {"page": page})
        for m in data.get("results", []):
            if m.get("id"):
                unique_ids.add(m["id"])

    logger.info(f"Collected {len(unique_ids)} unique IDs after Popular endpoint.")

    # 2. Top Rated (Pages 1 to 10)
    for page in range(1, 11):
        data = fetch_tmdb(client, "/movie/top_rated", {"page": page})
        for m in data.get("results", []):
            if m.get("id"):
                unique_ids.add(m["id"])

    logger.info(f"Collected {len(unique_ids)} unique IDs after Top Rated endpoint.")

    # 3. Now Playing (Pages 1 to 5)
    for page in range(1, 6):
        data = fetch_tmdb(client, "/movie/now_playing", {"page": page})
        for m in data.get("results", []):
            if m.get("id"):
                unique_ids.add(m["id"])

    # 4. Upcoming (Pages 1 to 5)
    for page in range(1, 6):
        data = fetch_tmdb(client, "/movie/upcoming", {"page": page})
        for m in data.get("results", []):
            if m.get("id"):
                unique_ids.add(m["id"])

    # 5. Discover per Major Genre (3 pages each)
    major_genres = [28, 35, 18, 878, 53, 27, 12, 10749, 16, 14, 9648, 80]
    for genre_id in major_genres:
        for page in range(1, 4):
            data = fetch_tmdb(client, "/discover/movie", {
                "with_genres": genre_id,
                "sort_by": "popularity.desc",
                "vote_count.gte": 50,
                "page": page
            })
            for m in data.get("results", []):
                if m.get("id"):
                    unique_ids.add(m["id"])

    logger.info(f"Total unique movie IDs collected across all endpoints: {len(unique_ids)}")
    return list(unique_ids)

def seed_from_tmdb(db: Session, target_count: int = 1200):
    logger.info("Starting live TMDB multi-discovery import...")
    with httpx.Client() as client:
        movie_ids = collect_movie_ids(client, target_count=target_count)

        imported_count = 0
        updated_count = 0
        total_to_process = len(movie_ids)

        for idx, tmdb_id in enumerate(movie_ids, 1):
            # Fetch movie details with appended credits and keywords
            data = fetch_tmdb(client, f"/movie/{tmdb_id}", {"append_to_response": "credits,keywords"})
            if not data or not data.get("title"):
                continue

            # Extract fields
            title = data.get("title", "").strip()
            overview = data.get("overview", "")
            release_date = data.get("release_date", "")
            runtime = data.get("runtime") or 0
            rating = round(data.get("vote_average", 0.0), 1)
            vote_count = data.get("vote_count", 0)
            popularity = round(data.get("popularity", 0.0), 1)
            original_language = data.get("original_language", "en")
            poster_path = data.get("poster_path") or ""
            backdrop_path = data.get("backdrop_path") or ""
            homepage = data.get("homepage") or ""
            tagline = data.get("tagline") or ""

            # Keywords
            kw_list = []
            keywords_data = data.get("keywords", {})
            for kw in keywords_data.get("keywords", []):
                kw_list.append(kw.get("name", ""))
            keywords_str = ", ".join(kw_list)

            # Check if movie already exists (idempotent upsert)
            movie = db.query(Movie).filter(Movie.tmdb_id == tmdb_id).first()
            is_new = False
            if not movie:
                movie = Movie(tmdb_id=tmdb_id)
                is_new = True

            movie.title = title
            movie.overview = overview
            movie.release_date = release_date
            movie.runtime = runtime
            movie.rating = rating
            movie.vote_count = vote_count
            movie.popularity = popularity
            movie.original_language = original_language
            movie.poster_path = poster_path
            movie.backdrop_path = backdrop_path
            movie.homepage = homepage
            movie.tagline = tagline
            movie.keywords = keywords_str

            if is_new:
                db.add(movie)
                db.flush()
                imported_count += 1
            else:
                updated_count += 1

            # Update Genres
            genre_objs = []
            for g in data.get("genres", []):
                g_name = g.get("name", "").strip()
                if g_name:
                    genre_objs.append(get_or_create_genre(db, g_name))
            movie.genres = genre_objs

            # Update Directors
            crew = data.get("credits", {}).get("crew", [])
            director_objs = []
            for member in crew:
                if member.get("job") == "Director":
                    d_name = member.get("name", "").strip()
                    if d_name:
                        director_objs.append(get_or_create_director(db, d_name))
            movie.directors = list({d.id: d for d in director_objs}.values()) # deduplicate

            # Update Cast associations
            movie.cast_associations.clear()
            cast_list = data.get("credits", {}).get("cast", [])[:8] # Top 8 billed actors
            for order, actor in enumerate(cast_list):
                actor_name = actor.get("name", "").strip()
                character_name = actor.get("character", "").strip()
                if actor_name:
                    cast_member = get_or_create_cast_member(db, actor_name)
                    cast_assoc = MovieCast(
                        movie_id=movie.id,
                        cast_member_id=cast_member.id,
                        cast_order=order,
                        character=character_name
                    )
                    db.add(cast_assoc)

            # Batch commit every 50 movies
            if idx % 50 == 0 or idx == total_to_process:
                db.commit()
                logger.info(f"Progress: [{idx}/{total_to_process}] movies processed. (New: {imported_count}, Updated: {updated_count})")

            # Small sleep to be a good API citizen
            time.sleep(0.05)

        db.commit()
        logger.info(f"Seeding finished successfully! Total New: {imported_count}, Total Updated: {updated_count}")

def seed_from_offline_dataset(db: Session):
    """Fallback: Seeds initial 100 movies from local movies.json if TMDB_API_KEY is missing."""
    json_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "movies.json"))
    if not os.path.exists(json_path):
        logger.warning(f"Offline dataset not found at {json_path}")
        return

    logger.info("Seeding database from offline movies.json dataset...")
    with open(json_path, "r", encoding="utf-8") as f:
        movies_data = json.load(f)

    imported_count = 0
    for m in movies_data:
        tmdb_id = m.get("id") or m.get("tmdb_id")
        movie = db.query(Movie).filter(Movie.tmdb_id == tmdb_id).first()
        is_new = False
        if not movie:
            movie = Movie(tmdb_id=tmdb_id)
            is_new = True

        movie.title = m.get("title", "")
        movie.overview = m.get("overview", "")
        movie.release_date = str(m.get("year", ""))
        movie.runtime = m.get("runtime", 120)
        movie.rating = float(m.get("rating", 0.0))
        movie.vote_count = int(m.get("popularity", 50) * 10)
        movie.popularity = float(m.get("popularity", 50.0))
        movie.original_language = m.get("language", "en").lower()
        movie.poster_path = m.get("poster", "")
        movie.backdrop_path = m.get("backdrop", "")
        movie.keywords = ", ".join(m.get("keywords", []))
        movie.mood = ", ".join(m.get("mood", []))

        if is_new:
            db.add(movie)
            db.flush()
            imported_count += 1

        # Genres
        genre_objs = []
        for g_name in m.get("genres", []):
            if g_name:
                genre_objs.append(get_or_create_genre(db, g_name))
        movie.genres = genre_objs

        # Director
        d_name = m.get("director", "").strip()
        if d_name:
            movie.directors = [get_or_create_director(db, d_name)]

        # Cast
        movie.cast_associations.clear()
        for order, actor_name in enumerate(m.get("cast", [])):
            if actor_name:
                cast_member = get_or_create_cast_member(db, actor_name)
                cast_assoc = MovieCast(
                    movie_id=movie.id,
                    cast_member_id=cast_member.id,
                    cast_order=order,
                    character=""
                )
                db.add(cast_assoc)

    db.commit()
    logger.info(f"Offline dataset seeding complete: {imported_count} movies inserted/updated into SQLite.")

def run_seed():
    init_db()
    db = SessionLocal()
    try:
        if TMDB_API_KEY:
            logger.info(f"TMDB_API_KEY detected. Fetching live multi-criteria movies...")
            seed_from_tmdb(db)
        else:
            logger.warning("="*70)
            logger.warning("No TMDB_API_KEY found in .env!")
            logger.warning("Seeding local 100-movie catalog into SQLite as fallback.")
            logger.warning("To import 1,000+ to 5,000+ movies, set TMDB_API_KEY in .env and run this script again.")
            logger.warning("="*70)
            seed_from_offline_dataset(db)
    finally:
        db.close()

if __name__ == "__main__":
    run_seed()
