# backend/services/recommendation.py
import logging
from typing import List, Dict, Set
from backend.data.movies import movies as local_movies
from backend.database import watchlist_collection

logger = logging.getLogger("uvicorn.error")

class HybridRecommender:
    def __init__(self):
        # Weights for Content-Based Metadata Overlaps
        self.feature_weights = {
            "genres": 0.4,
            "keywords": 0.3,
            "cast": 0.2,
            "director": 0.1
        }
        
        # Weights for Hybrid Combiner
        self.hybrid_weights = {
            "content": 0.5,
            "collaborative": 0.5
        }

    # Helper: Computes Jaccard Similarity between two sets
    def _jaccard_similarity(self, set_a: Set[str], set_b: Set[str]) -> float:
        if not set_a or not set_b:
            return 0.0
        intersection = len(set_a.intersection(set_b))
        union = len(set_a.union(set_b))
        return intersection / union if union > 0 else 0.0

    # Computes metadata similarity between two movie dict objects
    def get_movie_similarity(self, movie_a: dict, movie_b: dict) -> float:
        # 1. Genre Jaccard
        genres_a = set(movie_a.get("genres", []))
        genres_b = set(movie_b.get("genres", []))
        genre_sim = self._jaccard_similarity(genres_a, genres_b)

        # 2. Keywords Jaccard
        keywords_a = set(movie_a.get("keywords", []))
        keywords_b = set(movie_b.get("keywords", []))
        keyword_sim = self._jaccard_similarity(keywords_a, keywords_b)

        # 3. Cast Jaccard
        cast_a = set(movie_a.get("cast", []))
        cast_b = set(movie_b.get("cast", []))
        cast_sim = self._jaccard_similarity(cast_a, cast_b)

        # 4. Director Equality
        dir_a = movie_a.get("director", "").strip().lower()
        dir_b = movie_b.get("director", "").strip().lower()
        dir_sim = 1.0 if (dir_a and dir_b and dir_a == dir_b) else 0.0

        # Weighted Sum
        score = (
            self.feature_weights["genres"] * genre_sim +
            self.feature_weights["keywords"] * keyword_sim +
            self.feature_weights["cast"] * cast_sim +
            self.feature_weights["director"] * dir_sim
        )
        return score

    # Content-based recommendations: find similar movies to a specific movie
    def get_content_recommendations(self, movie_id: int, limit: int = 10) -> List[dict]:
        target = next((m for m in local_movies if m["id"] == movie_id), None)
        if not target:
            return []

        scored_movies = []
        for m in local_movies:
            if m["id"] == movie_id:
                continue
            sim = self.get_movie_similarity(target, m)
            scored_movies.append((m, sim))

        # Sort by similarity score descending
        scored_movies.sort(key=lambda item: item[1], reverse=True)
        return [item[0] for item in scored_movies[:limit]]

    # Hybrid recommendations: personalization based on watchlist and other users
    async def get_personalized_recommendations(self, user_id: str, limit: int = 12) -> List[dict]:
        # 1. Fetch current user's watchlist from MongoDB
        user_watch_doc = await watchlist_collection.find_one({"user_id": user_id})
        user_watchlist = user_watch_doc.get("movies", []) if user_watch_doc else []
        user_movie_ids = {m["id"] for m in user_watchlist}

        # Cold Start Handle: if watchlist is empty, recommend popular items
        if not user_movie_ids:
            logger.info(f"Cold Start: User {user_id} has empty watchlist. Recommending popular hits.")
            return sorted(local_movies, key=lambda m: m["popularity"], reverse=True)[:limit]

        # Resolve detailed movie structures for current user's watchlist
        seed_movies = [next((lm for lm in local_movies if lm["id"] == m_id), None) for m_id in user_movie_ids]
        seed_movies = [m for m in seed_movies if m]

        # 2. CONTENT-BASED SCORING
        # Score every movie in the local database (not already watchlisted) against the seed profile
        content_scores = {}
        for m in local_movies:
            if m["id"] in user_movie_ids:
                continue
            
            # Average similarity to all seed movies
            total_sim = sum(self.get_movie_similarity(m, seed) for seed in seed_movies)
            content_scores[m["id"]] = total_sim / len(seed_movies) if seed_movies else 0.0

        # 3. COLLABORATIVE FILTERING SCORING
        # Fetch watchlists for all other users
        cursor = watchlist_collection.find({"user_id": {"$ne": user_id}})
        other_watchlists = await cursor.to_list(length=1000)

        collaborative_scores = {}
        if other_watchlists:
            user_similarities = {}
            for doc in other_watchlists:
                o_user_id = doc["user_id"]
                o_movies = {m["id"] for m in doc.get("movies", [])}
                
                # Calculate Jaccard similarity between current user's watchlist and this user's watchlist
                sim = self._jaccard_similarity(user_movie_ids, o_movies)
                if sim > 0:
                    user_similarities[o_user_id] = sim

            # Score candidates based on similar users
            for doc in other_watchlists:
                o_user_id = doc["user_id"]
                if o_user_id not in user_similarities:
                    continue
                
                sim = user_similarities[o_user_id]
                for m in doc.get("movies", []):
                    m_id = m["id"]
                    if m_id in user_movie_ids:
                        continue # Already watched
                    
                    collaborative_scores[m_id] = collaborative_scores.get(m_id, 0.0) + sim

            # Normalize collaborative scores to [0.0, 1.0] range
            if collaborative_scores:
                max_val = max(collaborative_scores.values())
                if max_val > 0:
                    for m_id in collaborative_scores:
                        collaborative_scores[m_id] /= max_val

        # 4. HYBRID COMBINATION
        hybrid_scores = []
        for m in local_movies:
            m_id = m["id"]
            if m_id in user_movie_ids:
                continue
            
            content_score = content_scores.get(m_id, 0.0)
            collab_score = collaborative_scores.get(m_id, 0.0)
            
            # If collaborative data is available, compute hybrid. Else fall back entirely to content-based
            if collaborative_scores:
                final_score = (
                    self.hybrid_weights["content"] * content_score +
                    self.hybrid_weights["collaborative"] * collab_score
                )
            else:
                final_score = content_score

            # Boost slightly based on movie rating to reward high quality
            final_score += (m.get("rating", 0.0) / 100.0)

            hybrid_scores.append((m, final_score))

        # Sort and return
        hybrid_scores.sort(key=lambda item: item[1], reverse=True)
        
        # If the scores are very low (e.g. no metadata overlap), fill in with popular movies
        results = [item[0] for item in hybrid_scores[:limit]]
        if len(results) < limit:
            remaining = limit - len(results)
            populars = sorted(local_movies, key=lambda m: m["popularity"], reverse=True)
            for pm in populars:
                if pm["id"] not in user_movie_ids and pm not in results:
                    results.append(pm)
                    remaining -= 1
                    if remaining <= 0:
                        break

        return results

# Instantiate recommender
recommender = HybridRecommender()
