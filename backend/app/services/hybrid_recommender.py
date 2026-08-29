# backend/app/services/hybrid_recommender.py
import logging
from typing import List, Dict, Tuple, Optional, Set
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.app.models.movie import Movie
from backend.app.models.rating import Rating
from backend.app.models.user import WatchlistItem, User
from backend.app.services.tfidf_recommender import tfidf_engine
from backend.app.services.collaborative_recommender import collaborative_engine

logger = logging.getLogger("movie_app")

class HybridRecommender:
    """
    State-of-the-art Hybrid Recommendation Engine combining:
    1. Content-Based Filtering via Scikit-Learn TF-IDF vectorization & Cosine Similarity.
    2. Collaborative Filtering via SVD Matrix Factorization & Item-Item similarity.
    3. Bayesian Average Quality & Popularity priors.
    4. Adaptive dynamic weighting based on user interaction maturity (cold-start vs. power-user).
    """

    def __init__(self):
        pass

    def retrain_all(self, db: Session) -> dict:
        """
        Retrains both TF-IDF Content and Collaborative Filtering models with the latest database records.
        """
        tfidf_ok = tfidf_engine.fit(db)
        collab_ok = collaborative_engine.fit(db)
        return {
            "tfidf_trained": tfidf_ok,
            "collaborative_trained": collab_ok,
            "total_movies": len(tfidf_engine.movie_ids),
            "total_interactions": collaborative_engine.total_interactions
        }

    def get_personalized_recommendations(
        self,
        user_id: Optional[int],
        db: Session,
        limit: int = 12
    ) -> List[dict]:
        """
        Generates personalized hybrid recommendations for a user.
        If user is anonymous or has 0 interactions, gracefully falls back to Bayesian top-quality titles.
        """
        # Ensure engines are trained
        if not tfidf_engine.is_trained:
            tfidf_engine.fit(db)
        if not collaborative_engine.is_trained:
            collaborative_engine.fit(db)

        # 1. Fetch user's interactions (Ratings and Watchlist)
        user_ratings: Dict[int, float] = {}
        user_watchlist: Set[int] = set()

        if user_id:
            ratings = db.query(Rating).filter(Rating.user_id == user_id).all()
            for r in ratings:
                user_ratings[r.movie_id] = float(r.score)

            watchlists = db.query(WatchlistItem).filter(WatchlistItem.user_id == user_id).all()
            for w in watchlists:
                user_watchlist.add(w.movie_id)

        exclude_ids = set(user_ratings.keys()).union(user_watchlist)
        num_interactions = len(user_ratings) + len(user_watchlist)

        # 2. Cold-Start Handling (0 interactions)
        if num_interactions == 0:
            logger.info(f"[Hybrid Engine] Cold-start for user {user_id}. Delivering critically acclaimed blockbuster mix.")
            top_movies = db.query(Movie).filter(Movie.rating >= 7.8).order_by(desc(Movie.popularity)).limit(limit).all()
            results = []
            for m in top_movies:
                results.append({
                    "movie_id": m.id,
                    "movie": m,
                    "match_score": 90.0,
                    "hybrid_score": 0.90,
                    "content_score": 0.0,
                    "collab_score": 0.0,
                    "reasoning": f"Critically acclaimed ({m.rating}★) trending favorite with global audiences"
                })
            return results

        # 3. Compute Content-Based TF-IDF Scores
        content_recs = tfidf_engine.get_user_content_profile_recommendations(
            user_ratings=user_ratings,
            user_watchlist=user_watchlist,
            top_n=50,
            exclude_ids=exclude_ids
        )
        content_score_map: Dict[int, Tuple[float, str]] = {
            m_id: (score, exp) for m_id, score, exp in content_recs
        }

        # 4. Compute Collaborative Filtering Scores
        collab_recs = collaborative_engine.get_collaborative_recommendations(
            user_id=user_id if user_id else -1,
            top_n=50,
            exclude_ids=exclude_ids
        )
        collab_score_map: Dict[int, Tuple[float, str]] = {
            m_id: (score, exp) for m_id, score, exp in collab_recs
        }

        # 5. Determine Dynamic Adaptive Weights based on Interaction Density
        if num_interactions < 3:
            # Early user profile: Trust content matching heavily, small collab weight
            w_content = 0.70
            w_collab = 0.20
            w_quality = 0.10
        elif num_interactions < 8:
            # Maturing profile
            w_content = 0.50
            w_collab = 0.40
            w_quality = 0.10
        else:
            # Established power-user profile: Collaborative filtering is highly reliable
            w_content = 0.40
            w_collab = 0.50
            w_quality = 0.10

        # 6. Candidate Pool Assembly & Fusion
        all_candidate_ids = set(content_score_map.keys()).union(set(collab_score_map.keys()))

        # If candidates are sparse, fetch high-quality catalog titles as fill
        if len(all_candidate_ids) < limit * 2:
            catalog_movies = db.query(Movie).filter(Movie.id.notin_(exclude_ids)).order_by(desc(Movie.rating)).limit(30).all()
            for cm in catalog_movies:
                all_candidate_ids.add(cm.id)

        candidate_movies = db.query(Movie).filter(Movie.id.in_(all_candidate_ids)).all()
        scored_candidates = []

        for movie in candidate_movies:
            m_id = movie.id
            c_score, c_reason = content_score_map.get(m_id, (0.0, ""))
            cf_score, cf_reason = collab_score_map.get(m_id, (0.0, ""))

            # Quality prior normalized to [0, 1]
            q_score = min(1.0, max(0.0, (movie.rating - 5.0) / 5.0))

            # Hybrid Score formula
            hybrid_score = (w_content * c_score) + (w_collab * cf_score) + (w_quality * q_score)

            # Build explainable reasoning text
            reasons = []
            if c_score > 0.15 and c_reason:
                reasons.append(c_reason)
            if cf_score > 0.35 and cf_reason:
                reasons.append("Loved by users with matching taste")
            if movie.rating >= 8.2:
                reasons.append(f"Masterpiece rating ({movie.rating}★)")
            if not reasons:
                reasons.append("High thematic relevance to your library")

            explanation = " • ".join(reasons[:2])

            scored_candidates.append({
                "movie_id": m_id,
                "movie": movie,
                "hybrid_score": float(hybrid_score),
                "content_score": float(c_score),
                "collab_score": float(cf_score),
                "reasoning": explanation
            })

        # 7. Sort by Hybrid Score descending
        scored_candidates.sort(key=lambda x: x["hybrid_score"], reverse=True)
        top_candidates = scored_candidates[:limit]

        # 8. Scale display match percentage (78% to 99%)
        max_h = top_candidates[0]["hybrid_score"] if top_candidates and top_candidates[0]["hybrid_score"] > 0 else 1.0
        for item in top_candidates:
            normalized_pct = min(99.0, max(75.0, round((item["hybrid_score"] / max_h) * 98.0, 1)))
            item["match_score"] = normalized_pct

        return top_candidates

    def get_content_recommendations_for_movie(
        self,
        movie_id: int,
        db: Session,
        limit: int = 10
    ) -> List[dict]:
        """
        Returns top-N TF-IDF content recommendations for a single movie with match percentages.
        """
        if not tfidf_engine.is_trained:
            tfidf_engine.fit(db)

        sim_tuples = tfidf_engine.get_similar_movies(movie_id, top_n=limit)
        if not sim_tuples:
            return []

        sim_map = {m_id: (score, reason) for m_id, score, reason in sim_tuples}
        movie_ids = list(sim_map.keys())

        movies = db.query(Movie).filter(Movie.id.in_(movie_ids)).all()
        # Preserve similarity order
        movies_dict = {m.id: m for m in movies}

        results = []
        max_sim = sim_tuples[0][1] if sim_tuples and sim_tuples[0][1] > 0 else 1.0

        for m_id, score, reason in sim_tuples:
            if m_id in movies_dict:
                movie = movies_dict[m_id]
                pct = min(99.0, max(72.0, round((score / max_sim) * 98.0, 1)))
                results.append({
                    "movie": movie,
                    "match_score": pct,
                    "similarity": round(score, 3),
                    "reasoning": reason
                })

        return results

    def get_wizard_recommendations(
        self,
        genres: List[str],
        mood: str,
        era: str,
        min_rating: Optional[float],
        runtime: str,
        db: Session,
        limit: int = 12
    ) -> List[dict]:
        """
        Executes TF-IDF feature space query combined with hard/soft constraint scoring.
        """
        if not tfidf_engine.is_trained:
            tfidf_engine.fit(db)

        all_movies: List[Movie] = db.query(Movie).all()
        scored = []

        for m in all_movies:
            # 1. Genres (40 pts)
            m_genres = [g.name for g in m.genres]
            if genres:
                matched_genres = len(set(m_genres).intersection(set(genres)))
                genre_score = (matched_genres / len(genres)) * 40.0
            else:
                genre_score = 40.0

            # 2. Mood (25 pts)
            m_mood = (m.mood or "")
            mood_score = 25.0 if (not mood or mood.lower() in m_mood.lower()) else 0.0

            # 3. Rating (15 pts)
            rating_score = 15.0
            if min_rating:
                if m.rating >= min_rating:
                    rating_score = 15.0
                elif m.rating >= min_rating - 0.5:
                    rating_score = 8.0
                else:
                    rating_score = 0.0

            # 4. Era (10 pts)
            era_score = 10.0
            if era and m.release_date:
                try:
                    year = int(m.release_date.split("-")[0])
                    if era == "1980s" and (1980 <= year < 1990):
                        era_score = 10.0
                    elif era == "1990s" and (1990 <= year < 2000):
                        era_score = 10.0
                    elif era == "2000s" and (2000 <= year < 2010):
                        era_score = 10.0
                    elif era == "2010s" and (2010 <= year < 2020):
                        era_score = 10.0
                    elif era == "2020+" and (year >= 2020):
                        era_score = 10.0
                    else:
                        era_score = 3.0
                except Exception:
                    era_score = 5.0

            # 5. Runtime (10 pts)
            runtime_score = 10.0
            r = m.runtime or 120
            if runtime == "<90" and r < 90:
                runtime_score = 10.0
            elif runtime == "90-120" and (90 <= r <= 120):
                runtime_score = 10.0
            elif runtime == "120-150" and (120 < r <= 150):
                runtime_score = 10.0
            elif runtime == "150+" and r > 150:
                runtime_score = 10.0
            elif runtime:
                runtime_score = 4.0

            total_score = genre_score + mood_score + rating_score + era_score + runtime_score

            if total_score >= 35.0:
                scored.append((total_score, m))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:limit]

        results = []
        for s, movie in top:
            results.append({
                "movie": movie,
                "score": int(round(min(99.0, s)))
            })

        return results

# Singleton instance
hybrid_engine = HybridRecommender()
