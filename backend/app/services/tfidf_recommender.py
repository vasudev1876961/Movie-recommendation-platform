# backend/app/services/tfidf_recommender.py
import re
import logging
from typing import List, Dict, Tuple, Optional, Set
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session
from backend.app.models.movie import Movie

logger = logging.getLogger("movie_app")

class TFIDFRecommender:
    """
    Content-Based Recommendation Engine using TF-IDF (Term Frequency - Inverse Document Frequency)
    and Pairwise Cosine Similarity over rich cinematic metadata soup.
    """

    def __init__(self):
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix: Optional[np.ndarray] = None
        self.movie_ids: List[int] = []
        self.movie_id_to_idx: Dict[int, int] = {}
        self.idx_to_movie_id: Dict[int, int] = {}
        self.movie_metadata: Dict[int, dict] = {}
        self.is_trained: bool = False

    def _build_metadata_soup(self, movie: Movie) -> str:
        """
        Creates a rich entity-weighted metadata representation for the movie.
        Entity names are transformed into dedicated tokens (e.g. dir_christopher_nolan)
        to prevent generic word collisions and boost precision.
        """
        title = (movie.title or "").strip()
        overview = (movie.overview or "").strip()
        tagline = (movie.tagline or "").strip()
        keywords = (movie.keywords or "").replace(",", " ").strip()
        mood = (movie.mood or "").replace(",", " ").strip()

        # Entity-tokenized genres
        genres = [f"genre_{g.name.strip().lower().replace(' ', '_')}" for g in movie.genres if g.name]
        genres_str = (" " + " ".join(genres) + " ") * 4

        # Entity-tokenized directors
        directors = [f"dir_{d.name.strip().lower().replace(' ', '_')}" for d in movie.directors if d.name]
        directors_str = (" " + " ".join(directors) + " ") * 4

        # Entity-tokenized top 4 billed cast members
        cast_members = [
            f"actor_{assoc.cast_member.name.strip().lower().replace(' ', '_')}"
            for assoc in sorted(movie.cast_associations, key=lambda x: x.cast_order)[:4]
            if assoc.cast_member and assoc.cast_member.name
        ]
        cast_str = (" " + " ".join(cast_members) + " ") * 3

        soup = f"{title} {title} {genres_str} {directors_str} {cast_str} {mood} {keywords} {tagline} {overview}"
        # Normalize whitespace
        return re.sub(r'\s+', ' ', soup).strip()

    def fit(self, db: Session) -> bool:
        """
        Trains the TF-IDF vectorizer and precomputes the feature matrix for all movies in the catalog.
        """
        try:
            movies: List[Movie] = db.query(Movie).all()
            if not movies:
                logger.warning("[TF-IDF Engine] No movies found in database to train on.")
                return False

            self.movie_ids = []
            self.movie_id_to_idx = {}
            self.idx_to_movie_id = {}
            self.movie_metadata = {}
            corpus = []

            for idx, movie in enumerate(movies):
                self.movie_ids.append(movie.id)
                self.movie_id_to_idx[movie.id] = idx
                self.idx_to_movie_id[idx] = movie.id

                # Cache lightweight metadata for fast reason generation
                self.movie_metadata[movie.id] = {
                    "title": movie.title,
                    "rating": movie.rating,
                    "popularity": movie.popularity,
                    "genres": [g.name for g in movie.genres],
                    "directors": [d.name for d in movie.directors],
                    "cast": [assoc.cast_member.name for assoc in movie.cast_associations[:3] if assoc.cast_member]
                }

                soup = self._build_metadata_soup(movie)
                corpus.append(soup)

            # Initialize TF-IDF Vectorizer with unigrams and bigrams + sublinear scaling
            self.vectorizer = TfidfVectorizer(
                ngram_range=(1, 2),
                stop_words="english",
                sublinear_tf=True,
                max_features=15000,
                token_pattern=r'(?u)\b\w+\b'
            )

            self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
            self.is_trained = True
            logger.info(f"[TF-IDF Engine] Successfully fitted TF-IDF matrix ({self.tfidf_matrix.shape[0]} movies x {self.tfidf_matrix.shape[1]} features).")
            return True

        except Exception as e:
            logger.error(f"[TF-IDF Engine] Training failed: {e}", exc_info=True)
            self.is_trained = False
            return False

    def get_similar_movies(self, movie_id: int, top_n: int = 10, min_similarity: float = 0.005) -> List[Tuple[int, float, str]]:
        """
        Finds the top N most similar movies to a given movie using TF-IDF cosine similarity.
        Returns: List of tuples (movie_id, similarity_score_0_to_1, explanation_reason)
        """
        if not self.is_trained or self.tfidf_matrix is None or self.vectorizer is None:
            return []

        if movie_id not in self.movie_id_to_idx:
            return []

        target_idx = self.movie_id_to_idx[movie_id]
        target_vec = self.tfidf_matrix[target_idx]

        # Compute cosine similarity against all movies
        similarities = cosine_similarity(target_vec, self.tfidf_matrix).flatten()

        # Sort indices by similarity descending
        ranked_indices = np.argsort(similarities)[::-1]

        results: List[Tuple[int, float, str]] = []
        target_meta = self.movie_metadata.get(movie_id, {})

        for idx in ranked_indices:
            candidate_id = self.idx_to_movie_id[idx]
            if candidate_id == movie_id:
                continue

            score = float(similarities[idx])
            if score < min_similarity:
                continue


            cand_meta = self.movie_metadata.get(candidate_id, {})
            
            # Generate explainable reasons based on overlap
            common_genres = set(target_meta.get("genres", [])).intersection(set(cand_meta.get("genres", [])))
            common_directors = set(target_meta.get("directors", [])).intersection(set(cand_meta.get("directors", [])))
            common_cast = set(target_meta.get("cast", [])).intersection(set(cand_meta.get("cast", [])))

            reasons = []
            if common_directors:
                reasons.append(f"Same director ({list(common_directors)[0]})")
            if common_cast:
                reasons.append(f"Stars {list(common_cast)[0]}")
            if common_genres:
                reasons.append(f"Shared genres ({', '.join(list(common_genres)[:2])})")
            if not reasons:
                reasons.append("Thematic & narrative harmony")

            explanation = " • ".join(reasons)
            results.append((candidate_id, score, explanation))

            if len(results) >= top_n:
                break

        return results

    def get_user_content_profile_recommendations(
        self,
        user_ratings: Dict[int, float],
        user_watchlist: Set[int],
        top_n: int = 15,
        exclude_ids: Optional[Set[int]] = None
    ) -> List[Tuple[int, float, str]]:
        """
        Creates a composite user taste vector by aggregating the TF-IDF vectors of movies the user
        has rated (weighted by rating score) or watchlisted.
        Returns: List of tuples (movie_id, normalized_content_score_0_to_1, explanation)
        """
        if not self.is_trained or self.tfidf_matrix is None:
            return []

        if exclude_ids is None:
            exclude_ids = set()

        all_interactions = set(user_ratings.keys()).union(user_watchlist)
        exclude_ids = exclude_ids.union(all_interactions)

        if not all_interactions:
            return []

        # Construct aggregate user profile vector in TF-IDF space
        n_features = self.tfidf_matrix.shape[1]
        user_vector = np.zeros((1, n_features), dtype=np.float32)
        total_weight = 0.0

        # Process explicit ratings
        for movie_id, score in user_ratings.items():
            if movie_id in self.movie_id_to_idx:
                idx = self.movie_id_to_idx[movie_id]
                # Normalized weight centered around 5.0 (range 1-10 -> weight -0.8 to +1.0)
                weight = (score - 5.0) / 5.0
                if weight > 0:
                    vec = self.tfidf_matrix[idx].toarray()
                    user_vector += weight * vec
                    total_weight += weight

        # Process implicit watchlist additions
        for movie_id in user_watchlist:
            if movie_id not in user_ratings and movie_id in self.movie_id_to_idx:
                idx = self.movie_id_to_idx[movie_id]
                weight = 0.6  # Standard positive affinity for watchlist items
                vec = self.tfidf_matrix[idx].toarray()
                user_vector += weight * vec
                total_weight += weight

        if total_weight <= 0.0:
            return []

        # Normalize user vector
        norm = np.linalg.norm(user_vector)
        if norm > 0:
            user_vector = user_vector / norm

        # Compute cosine similarities between user profile vector and all candidate movies
        similarities = cosine_similarity(user_vector, self.tfidf_matrix).flatten()

        ranked_indices = np.argsort(similarities)[::-1]
        results: List[Tuple[int, float, str]] = []

        for idx in ranked_indices:
            candidate_id = self.idx_to_movie_id[idx]
            if candidate_id in exclude_ids:
                continue

            score = float(similarities[idx])
            cand_meta = self.movie_metadata.get(candidate_id, {})
            genres_str = ", ".join(cand_meta.get("genres", [])[:2])
            explanation = f"Matches your taste profile in {genres_str or 'cinema'}"

            results.append((candidate_id, score, explanation))
            if len(results) >= top_n:
                break

        return results

# Singleton instance
tfidf_engine = TFIDFRecommender()
