import logging
import httpx
from fastapi import APIRouter, Query, HTTPException, status
from typing import List, Optional
from backend.config import settings
from backend.data.movies import movies as local_movies
from backend.models.user import UserPreferences

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/api/movies", tags=["Movies"])

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
  878: "Sci-Fi",
  10770: "TV Movie",
  53: "Thriller",
  10752: "War",
  37: "Western"
}

def is_api_active() -> bool:
    return len(settings.tmdb_api_key.strip()) > 0

def map_tmdb_movie(m: dict) -> dict:
    release_date = m.get("release_date", "")
    year = int(release_date.split("-")[0]) if release_date else 0
    
    genre_ids = m.get("genre_ids", [])
    genres = [GENRE_MAP[g_id] for g_id in genre_ids if g_id in GENRE_MAP]
    if not genres:
        genres = ["Drama"]
        
    moods = []
    if "Action" in genres or "Adventure" in genres:
        moods.extend(["Epic", "Adrenaline Rush"])
    if "Sci-Fi" in genres or "Mystery" in genres:
        moods.append("Mind-bending")
    if "Comedy" in genres:
        moods.extend(["Funny", "Light & Fun"])
    if "Drama" in genres:
        moods.append("Emotional")
    if "Romance" in genres:
        moods.append("Romantic")
    if "Horror" in genres:
        moods.extend(["Dark", "Spooky"])
    if "Family" in genres:
        moods.extend(["Feel Good", "Family"])
    if not moods:
        moods.append("Feel Good")

    return {
        "id": m["id"],
        "title": m["title"],
        "year": year,
        "rating": round(m.get("vote_average", 0.0), 1),
        "genres": genres,
        "runtime": m.get("runtime", 120),
        "overview": m.get("overview", "No description available."),
        "cast": [],
        "director": "",
        "language": m.get("original_language", "EN").upper(),
        "country": "",
        "poster": m.get("poster_path") or "",
        "backdrop": m.get("backdrop_path") or "",
        "mood": list(set(moods)),
        "trailer": "",
        "popularity": m.get("popularity", 0.0),
        "keywords": [w for w in (m["title"] + " " + m.get("overview", "")).lower().split() if len(w) > 4]
    }

async def fetch_tmdb(endpoint: str, params: dict = {}) -> Optional[dict]:
    url = f"https://api.themoviedb.org/3{endpoint}"
    query_params = {
        "api_key": settings.tmdb_api_key,
        **params
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=query_params)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"TMDb API error status={response.status_code} detail={response.text}")
                return None
        except Exception as e:
            logger.error(f"TMDb connection failed: {e}")
            return None

@router.get("/trending")
async def get_trending():
    if not is_api_active():
        return sorted(local_movies, key=lambda m: m["popularity"], reverse=True)[:15]
    
    data = await fetch_tmdb("/trending/movie/day")
    if data and "results" in data:
        return [map_tmdb_movie(m) for m in data["results"]]
    return local_movies[:15]

@router.get("/popular")
async def get_popular():
    if not is_api_active():
        return sorted(local_movies, key=lambda m: m["popularity"], reverse=True)[5:20]
    
    data = await fetch_tmdb("/movie/popular")
    if data and "results" in data:
        return [map_tmdb_movie(m) for m in data["results"]]
    return local_movies[5:20]

@router.get("/top-rated")
async def get_top_rated():
    if not is_api_active():
        return sorted(local_movies, key=lambda m: m["rating"], reverse=True)[:15]
    
    data = await fetch_tmdb("/movie/top_rated")
    if data and "results" in data:
        return [map_tmdb_movie(m) for m in data["results"]]
    return local_movies[:15]

@router.get("/hidden-gems")
async def get_hidden_gems():
    if not is_api_active():
        return [m for m in local_movies if m["rating"] >= 7.5 and m["popularity"] < 85][:15]
        
    data = await fetch_tmdb("/discover/movie", {
        "vote_average.gte": 7.5,
        "vote_count.gte": 100,
        "vote_count.lte": 800,
        "sort_by": "popularity.asc"
    })
    if data and "results" in data:
        return [map_tmdb_movie(m) for m in data["results"]]
    return [m for m in local_movies if m["rating"] >= 7.5 and m["popularity"] < 85][:15]

@router.get("/search")
async def search_movies(q: str = Query("")):
    if not q.strip():
        return []
        
    if not is_api_active():
        q_lower = q.lower()
        return [m for m in local_movies if q_lower in m["title"].lower() or q_lower in m["overview"].lower() or any(q_lower in g.lower() for g in m["genres"])]
        
    data = await fetch_tmdb("/search/movie", {"query": q})
    if data and "results" in data:
        return [map_tmdb_movie(m) for m in data["results"]]
    return []

@router.get("/{movie_id}")
async def get_details(movie_id: int):
    # Check if this belongs to local movie space (IDs < 1000)
    if not is_api_active() or movie_id < 1000:
        local = next((m for m in local_movies if m["id"] == movie_id), None)
        if local:
            return local
        raise HTTPException(status_code=404, detail="Movie not found locally")
        
    data = await fetch_tmdb(f"/movie/{movie_id}", {"append_to_response": "credits,videos"})
    if data:
        movie = map_tmdb_movie(data)
        movie["runtime"] = data.get("runtime") or 120
        
        if "production_countries" in data and data["production_countries"]:
            movie["country"] = data["production_countries"][0].get("name", "")
            
        credits = data.get("credits", {})
        if credits:
            movie["cast"] = [c["name"] for c in credits.get("cast", [])[:5]]
            director_info = next((c["name"] for c in credits.get("crew", []) if c.get("job") == "Director"), "Unknown")
            movie["director"] = director_info
            
        videos = data.get("videos", {})
        if videos:
            trailer_info = next((v["key"] for v in videos.get("results", []) if v.get("type") == "Trailer" and v.get("site") == "YouTube"), "")
            movie["trailer"] = trailer_info
            
        if "genres" in data:
            movie["genres"] = [g["name"] for g in data["genres"]]
            
        return movie
        
    raise HTTPException(status_code=404, detail="Movie details not found")

@router.get("/{movie_id}/recommendations")
async def get_recommendations(movie_id: int):
    if not is_api_active() or movie_id < 1000:
        # Fallback local recommendation overlap logic
        source = next((m for m in local_movies if m["id"] == movie_id), None)
        if not source:
            return []
        
        scored = []
        for m in local_movies:
            if m["id"] == source["id"]:
                continue
            overlap = len(set(m["genres"]).intersection(set(source["genres"])))
            scored.append((m, overlap))
            
        scored.sort(key=lambda item: item[1], reverse=True)
        return [item[0] for item in scored[:10]]

    data = await fetch_tmdb(f"/movie/{movie_id}/recommendations")
    if data and "results" in data:
        return [map_tmdb_movie(m) for m in data["results"][:10]]
    return []

@router.post("/recommendations/wizard")
async def get_wizard_recommendations(prefs: UserPreferences):
    scored_list = []
    
    for movie in local_movies:
        # 1. Genres (40 pts)
        genre_score = 0
        if prefs.genres:
            matched = len(set(movie["genres"]).intersection(set(prefs.genres)))
            genre_score = (matched / len(prefs.genres)) * 40
        else:
            genre_score = 40
            
        # 2. Mood (25 pts)
        mood_score = 25 if (not prefs.mood or prefs.mood in movie["mood"]) else 0
        
        # 3. Rating (15 pts)
        rating_score = 15
        if prefs.minRating:
            min_val = float(prefs.minRating)
            if movie["rating"] >= min_val:
                rating_score = 15
            elif movie["rating"] >= min_val - 0.5:
                rating_score = 7.5
            else:
                rating_score = 0
                
        # 4. Era (10 pts)
        era_score = 10
        if prefs.era:
            year = movie["year"]
            matches_era = False
            close_match = False
            
            if prefs.era == "1980s":
                matches_era = 1980 <= year < 1990
                close_match = 1975 <= year < 1995
            elif prefs.era == "1990s":
                matches_era = 1990 <= year < 2000
                close_match = 1985 <= year < 2005
            elif prefs.era == "2000s":
                matches_era = 2000 <= year < 2010
                close_match = 1995 <= year < 2015
            elif prefs.era == "2010s":
                matches_era = 2010 <= year < 2020
                close_match = 2005 <= year < 2025
            elif prefs.era == "2020+":
                matches_era = year >= 2020
                close_match = year >= 2015
                
            if matches_era:
                era_score = 10
            elif close_match:
                era_score = 5
            else:
                era_score = 0
                
        # 5. Runtime (10 pts)
        runtime_score = 10
        if prefs.runtime:
            r = movie["runtime"]
            matches_run = False
            close_run = False
            
            if prefs.runtime == "<90":
                matches_run = r < 90
                close_run = r <= 100
            elif prefs.runtime == "90-120":
                matches_run = 90 <= r <= 120
                close_run = 80 <= r <= 130
            elif prefs.runtime == "120-150":
                matches_run = 120 < r <= 150
                close_run = 110 <= r <= 160
            elif prefs.runtime == "150+":
                matches_run = r > 150
                close_run = r >= 135
                
            if matches_run:
                runtime_score = 10
            elif close_run:
                runtime_score = 5
            else:
                runtime_score = 0
                
        total = round(genre_score + mood_score + rating_score + era_score + runtime_score)
        
        if total > 10:
            scored_list.append({
                "movie": movie,
                "score": total
            })
            
    scored_list.sort(key=lambda item: item["score"], reverse=True)
    return scored_list[:12]
