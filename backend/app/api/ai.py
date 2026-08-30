# backend/app/api/ai.py
import re
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database.database import get_db
from backend.app.models.movie import Movie
from backend.app.schemas.movie import MovieListItem
from backend.app.api.movies import format_movie_list_item
from backend.app.services.semantic_search import semantic_search_engine

router = APIRouter(prefix="/api/ai", tags=["AI Recommendation Assistant"])

class AIRecommendRequest(BaseModel):
    query: str
    limit: Optional[int] = 6

class AIRecommendedMovie(BaseModel):
    movie: MovieListItem
    match_score: float
    reasoning: str

class AIRecommendResponse(BaseModel):
    query: str
    summary: str
    recommendations: List[AIRecommendedMovie]

GENRE_SYNONYMS = {
    "scifi": "Science Fiction",
    "sci-fi": "Science Fiction",
    "space": "Science Fiction",
    "futuristic": "Science Fiction",
    "action": "Action",
    "fight": "Action",
    "comedy": "Comedy",
    "funny": "Comedy",
    "drama": "Drama",
    "emotional": "Drama",
    "thriller": "Thriller",
    "suspense": "Thriller",
    "crime": "Crime",
    "mafia": "Crime",
    "animation": "Animation",
    "animated": "Animation",
    "cartoon": "Animation",
    "horror": "Horror",
    "scary": "Horror",
    "adventure": "Adventure",
    "fantasy": "Fantasy",
    "magic": "Fantasy",
    "superhero": "Action",
    "marvel": "Action",
    "romance": "Romance",
    "love": "Romance"
}

MOOD_KEYWORDS = {
    "mind-bending": ["dream", "reality", "time", "dimension", "subconscious", "multiverse", "simulation"],
    "dark": ["crime", "joker", "serial killer", "violence", "grim", "gotham"],
    "emotional": ["family", "hope", "love", "daughter", "sacrifice", "father", "friendship"],
    "epic": ["war", "universe", "battle", "destiny", "empire", "avengers", "thanos"],
    "funny": ["comedy", "humor", "hilarious", "parody", "satire", "fun"],
    "intense": ["survival", "danger", "race", "heist", "pursuit", "adrenaline"]
}

@router.post("/recommend", response_model=AIRecommendResponse)
def get_ai_recommendations(data: AIRecommendRequest, db: Session = Depends(get_db)):
    query = data.query.strip()
    if not query:
        return AIRecommendResponse(query="", summary="Please provide a movie prompt.", recommendations=[])

    # 1. Try Phase 4 Deep Neural Vector Search first
    if not semantic_search_engine.is_trained:
        semantic_search_engine.fit(db)

    neural_results = semantic_search_engine.search(
        query=query,
        top_k=data.limit or 6,
        min_score=0.15
    )

    if neural_results:
        movie_ids = [r["movie_id"] for r in neural_results]
        movies = db.query(Movie).filter(Movie.id.in_(movie_ids)).all()
        movie_map = {m.id: m for m in movies}

        recommendations = []
        for r in neural_results:
            m = movie_map.get(r["movie_id"])
            if m:
                recommendations.append(AIRecommendedMovie(
                    movie=format_movie_list_item(m),
                    match_score=r["match_score"],
                    reasoning=r["reasoning"]
                ))

        summary = f"Identified {len(recommendations)} matches using Neural Transformer embeddings (Sentence-Transformers) for \"{query}\"."
        return AIRecommendResponse(
            query=query,
            summary=summary,
            recommendations=recommendations
        )

    # 2. Heuristic fallback if neural search returned 0 items
    q_lower = query.lower()
    words = set(re.findall(r'\b[a-z0-9\-]+\b', q_lower))
    target_genres = set(GENRE_SYNONYMS[w] for w in words if w in GENRE_SYNONYMS)

    all_movies = db.query(Movie).all()
    scored = []

    for movie in all_movies:
        score = 0.0
        reasons = []

        m_title = movie.title.lower()
        m_overview = (movie.overview or "").lower()
        m_keywords = (movie.keywords or "").lower()
        m_genres = [g.name for g in movie.genres]
        m_directors = [d.name.lower() for d in movie.directors]
        m_cast = [assoc.cast_member.name.lower() for assoc in movie.cast_associations]

        for word in words:
            if len(word) > 2:
                if word in m_title:
                    score += 25.0
                    reasons.append(f"Title matches '{word}'")
                if word in m_keywords:
                    score += 15.0
                    reasons.append(f"Shares theme '{word}'")
                if word in m_overview:
                    score += 8.0
                if any(word in d for d in m_directors):
                    score += 20.0
                    reasons.append("Directed by requested creator")
                if any(word in c for c in m_cast):
                    score += 15.0
                    reasons.append("Features requested cast member")

        genre_matches = [g for g in m_genres if g in target_genres]
        if genre_matches:
            score += len(genre_matches) * 18.0
            reasons.append(f"Matches genre: {', '.join(genre_matches)}")

        for mood, terms in MOOD_KEYWORDS.items():
            if mood in q_lower or any(t in q_lower for t in terms):
                matched_terms = [t for t in terms if t in m_overview or t in m_keywords]
                if matched_terms:
                    score += len(matched_terms) * 10.0
                    reasons.append(f"Delivers {mood} vibes ({', '.join(matched_terms[:2])})")

        quality_score = (movie.rating * 2.0) + (min(movie.popularity, 100.0) * 0.1)
        total_score = round(score + quality_score, 1)

        if not reasons:
            top_genre = m_genres[0] if m_genres else "Cinema"
            reasons.append(f"Critically acclaimed {top_genre} with a {movie.rating} rating")

        unique_reasons = list(dict.fromkeys(reasons))
        scored.append((total_score, movie, " • ".join(unique_reasons[:3])))

    scored.sort(key=lambda x: x[0], reverse=True)
    top_picks = scored[:data.limit]

    max_score = top_picks[0][0] if top_picks else 1.0
    recommendations = []
    for s, movie, exp in top_picks:
        pct = min(99.0, max(75.0, round((s / max(max_score, 1.0)) * 98.0, 1)))
        recommendations.append(AIRecommendedMovie(
            movie=format_movie_list_item(movie),
            match_score=pct,
            reasoning=exp
        ))

    summary = f"Found {len(recommendations)} curated titles matching your request for '{data.query}' based on thematic mood and critical reception."

    return AIRecommendResponse(
        query=data.query,
        summary=summary,
        recommendations=recommendations
    )
