# backend/app/api/trailers.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.app.database.database import get_db
from backend.app.models.movie import Movie
from backend.app.schemas.trailer import (
    TrailerAnalysisResponse,
    TrailerTwinsResponse,
    TrailerVibeQuery,
    TrailerTwinItem
)
from backend.app.services.trailer_intelligence import trailer_intelligence

router = APIRouter(prefix="/api/trailers", tags=["Multimodal Trailer Intelligence"])

@router.get("/{movie_id}/analysis", response_model=TrailerAnalysisResponse)
def get_trailer_analysis(movie_id: int, db: Session = Depends(get_db)):
    """
    Returns full multimodal cinematic trailer analysis including:
    - 4-act structural segmentation (Exposition, Escalation, Climax, Stinger)
    - Sensory & emotional telemetry curves (tension, cuts/min velocity, audio decibels, visual lumens)
    - Aesthetic DNA (5-color harmonic keyframe palette, aspect ratio, camera movement, lighting key)
    - Content & spoiler safety classification
    """
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail=f"Movie with ID {movie_id} not found.")

    return trailer_intelligence.analyze_trailer(movie)

@router.get("/{movie_id}/twins", response_model=TrailerTwinsResponse)
def get_sensory_trailer_twins(
    movie_id: int,
    limit: int = Query(default=5, ge=1, le=15),
    db: Session = Depends(get_db)
):
    """
    Discovers movies whose trailers share the closest multimodal sensory trajectory,
    cadence of cuts, audio intensity crescendo, and emotional arc.
    """
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail=f"Movie with ID {movie_id} not found.")

    return trailer_intelligence.find_sensory_twins(movie_id, db=db, limit=limit)

@router.post("/vibe-search", response_model=List[TrailerTwinItem])
def search_trailers_by_vibe(query: TrailerVibeQuery, db: Session = Depends(get_db)):
    """
    Filters and ranks trailers based on desired sensory and affective pacing constraints
    (e.g., minimum adrenaline, high-tension crescendo, or contemplative awe).
    """
    movies = db.query(Movie).limit(40).all()
    results = []

    for m in movies:
        analysis = trailer_intelligence.analyze_trailer(m)
        telem = analysis.telemetry
        if not telem:
            continue

        max_ten = max(p.tension for p in telem)
        avg_adr = sum(p.affective_vector.get("adrenaline", 0) for p in telem) / len(telem) * 100.0
        avg_awe = sum(p.affective_vector.get("awe", 0) for p in telem) / len(telem) * 100.0

        if query.min_tension and max_ten < query.min_tension:
            continue
        if query.min_adrenaline and avg_adr < query.min_adrenaline:
            continue
        if query.min_awe and avg_awe < query.min_awe:
            continue

        score = round((max_ten * 0.4 + avg_adr * 0.3 + avg_awe * 0.3), 1)
        results.append(TrailerTwinItem(
            movie_id=m.id,
            title=m.title,
            year=m.release_date.split("-")[0] if m.release_date else "",
            rating=m.rating or 0.0,
            poster_path=m.poster_path,
            trailer_key=m.trailer,
            sensory_similarity_score=min(99.0, score),
            matching_pacing=analysis.overall_pacing,
            shared_affective_tone=analysis.acts[2].dominant_mood
        ))

    results.sort(key=lambda x: x.sensory_similarity_score, reverse=True)
    return results[:query.limit or 8]
