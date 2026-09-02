# backend/app/services/agents/strategist_agent.py
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from backend.app.services.agents.base_agent import BaseAgent
from backend.app.schemas.agents import ViewingDossier, DoubleFeaturePairing, AgentMessage
from backend.app.models.movie import Movie
from backend.app.services.semantic_search import semantic_search_engine

class ViewingStrategistAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="strategist_agent_vesper",
            name="Vesper",
            role="Viewing Strategist & Experience Curator",
            avatar="🍿",
            accent_color="#6366f1",
            description="Designs the optimal real-world viewing experience, pairs double-feature companion films, and curates atmospheric ambiance."
        )

    def formulate_viewing_dossier(
        self,
        movie: Movie,
        db: Session,
        exclude_ids: List[int]
    ) -> ViewingDossier:
        """Formulates viewing environment, atmosphere, and double feature pairing."""
        genres = [g.name for g in movie.genres]
        runtime = movie.runtime or 120
        rating = movie.rating or 7.5

        # 1. Optimal Setting
        if any(g in ["Horror", "Mystery", "Thriller"] for g in genres):
            optimal_setting = "Late-night solo viewing with studio headphones and lights dimmed"
            target_vibe = "Intense suspense and psychological immersion"
            snack_atmosphere = "Dark roast espresso or hot tea with low amber lighting"
        elif any(g in ["Science Fiction"] for g in genres):
            optimal_setting = "Distraction-free home cinema setting with wide aspect ratio screen"
            target_vibe = "Cosmic wonder, temporal philosophy, and visual awe"
            snack_atmosphere = "Light gourmet popcorn and zero-glare ambient backlighting"
        elif any(g in ["Action", "Adventure"] for g in genres):
            optimal_setting = "Friday night living room watch with soundbar volume cranked up"
            target_vibe = "High-octane adrenaline and collective thrills"
            snack_atmosphere = "Buttery theater popcorn, chilled drinks, and surround audio"
        elif any(g in ["Animation", "Family", "Comedy"] for g in genres):
            optimal_setting = "Relaxed weekend afternoon watch with friends or family"
            target_vibe = "Heartwarming laughter, comfort, and creative animation joy"
            snack_atmosphere = "Artisanal sweet treats and cozy blanket setup"
        else:
            optimal_setting = "Evening focused viewing in a comfortable, quiet sanctuary"
            target_vibe = "Deep emotional and character-driven contemplation"
            snack_atmosphere = "Fine dark chocolate and soothing warm beverage"

        runtime_slot = f"{runtime} min feature &bull; Ideal for prime-time immersion"

        # 2. Find Double-Feature Companion Film
        double_feature = None
        try:
            # Query semantic twin or genre sibling
            twins = semantic_search_engine.get_similar_movies(movie.id, top_k=5)
            companion_movie = None
            for t in twins:
                if t["movie_id"] != movie.id and t["movie_id"] not in exclude_ids:
                    c_m = db.query(Movie).filter(Movie.id == t["movie_id"]).first()
                    if c_m:
                        companion_movie = c_m
                        break

            if not companion_movie:
                # Fallback to genre overlap
                companion_movie = (
                    db.query(Movie)
                    .filter(Movie.id != movie.id, Movie.id.notin_(exclude_ids))
                    .order_by(Movie.rating.desc())
                    .first()
                )

            if companion_movie:
                raw_p = companion_movie.poster_path or companion_movie.poster or ""
                p_url = raw_p if raw_p.startswith("http") else (f"https://image.tmdb.org/t/p/w200{raw_p}" if raw_p else None)
                comp_year = int(companion_movie.release_date.split("-")[0]) if companion_movie.release_date and "-" in companion_movie.release_date else None
                
                double_feature = DoubleFeaturePairing(
                    movie_id=companion_movie.id,
                    title=companion_movie.title,
                    poster_path=p_url,
                    year=comp_year,
                    rating=companion_movie.rating,
                    pairing_rationale=f"Pairs seamlessly with {movie.title} by exploring complementary thematic depth and stylistic tone.",
                    transition_theme=f"Thematic Progression: From {movie.title} into {companion_movie.title}"
                )
        except Exception:
            pass

        return ViewingDossier(
            optimal_setting=optimal_setting,
            target_vibe=target_vibe,
            snack_atmosphere_pairing=snack_atmosphere,
            recommended_runtime_slot=runtime_slot,
            double_feature=double_feature
        )

    def enhance_candidates(
        self,
        consensus_candidates: List[Dict[str, Any]],
        db: Session
    ) -> Tuple[List[Dict[str, Any]], AgentMessage]:
        """Adds viewing dossiers and companion double features to all consensus candidates."""
        all_ids = [c["movie"].id for c in consensus_candidates]
        enhanced = []

        for c in consensus_candidates:
            movie = c["movie"]
            dossier = self.formulate_viewing_dossier(movie, db, exclude_ids=all_ids)
            c_copy = dict(c)
            c_copy["viewing_dossier"] = dossier
            enhanced.append(c_copy)

        msg_content = (
            f"🍿 **Viewing Strategies & Double Features Prepared**: Crafted atmospheric setting guides, "
            f"sound profiles, and double-feature companion pairings for all {len(enhanced)} top selections. "
            f"The Multi-Agent Consensus Dossier is complete and ready for presentation."
        )

        agent_msg = self.create_message(
            round_index=5,
            message_type="strategist_plan",
            content=msg_content,
            confidence=0.97
        )

        return enhanced, agent_msg
