# backend/app/services/collaborative_recommender.py
import logging
from typing import Dict, List, Tuple, Optional, Set
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import svds
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session
from backend.app.models.rating import Rating
from backend.app.models.user import WatchlistItem, User
from backend.app.models.movie import Movie

logger = logging.getLogger("movie_app")

class CollaborativeRecommender:
    """
    Collaborative Filtering Recommender Engine using:
    1. Matrix Factorization via Singular Value Decomposition (SVD) for global latent factor learning.
    2. Item-Item Collaborative Filtering for co-rated item affinity and explanation generation.
    """

    def __init__(self, n_factors: int = 10):
        self.n_factors = n_factors
        self.user_ids: List[int] = []
        self.movie_ids: List[int] = []
        self.user_to_idx: Dict[int, int] = {}
        self.idx_to_user: Dict[int, int] = {}
        self.movie_to_idx: Dict[int, int] = {}
        self.idx_to_movie: Dict[int, int] = {}
        
        # SVD reconstructed ratings matrix
        self.predicted_ratings_matrix: Optional[np.ndarray] = None
        # Item-Item similarity matrix
        self.item_similarity_matrix: Optional[np.ndarray] = None
        # Raw user-item matrix
        self.user_item_matrix: Optional[np.ndarray] = None

        self.is_trained: bool = False
        self.total_interactions: int = 0

    def fit(self, db: Session) -> bool:
        """
        Builds user-item interaction matrix from explicit ratings and implicit watchlists,
        then fits SVD matrix factorization and item-item similarity models.
        """
        try:
            # 1. Fetch all explicit ratings
            ratings: List[Rating] = db.query(Rating).all()
            
            # 2. Fetch all watchlists (implicit positive feedback)
            watchlists: List[WatchlistItem] = db.query(WatchlistItem).all()

            interaction_records = []

            for r in ratings:
                interaction_records.append({
                    "user_id": r.user_id,
                    "movie_id": r.movie_id,
                    "score": float(r.score) # 1.0 - 10.0
                })

            # Add watchlisted items if no explicit rating exists
            rated_pairs = {(r.user_id, r.movie_id) for r in ratings}
            for w in watchlists:
                if (w.user_id, w.movie_id) not in rated_pairs:
                    interaction_records.append({
                        "user_id": w.user_id,
                        "movie_id": w.movie_id,
                        "score": 7.5 # Default positive implicit rating
                    })

            self.total_interactions = len(interaction_records)

            if len(interaction_records) < 3:
                logger.info(f"[Collaborative Engine] Sparse interaction data ({len(interaction_records)} records). Engine initialized in fallback mode.")
                self.is_trained = False
                return False

            df = pd.DataFrame(interaction_records)

            # Build index maps
            self.user_ids = sorted(df["user_id"].unique().tolist())
            self.movie_ids = sorted(df["movie_id"].unique().tolist())

            self.user_to_idx = {u: i for i, u in enumerate(self.user_ids)}
            self.idx_to_user = {i: u for i, u in enumerate(self.user_ids)}
            self.movie_to_idx = {m: i for i, m in enumerate(self.movie_ids)}
            self.idx_to_movie = {i: m for i, m in enumerate(self.movie_ids)}

            n_users = len(self.user_ids)
            n_movies = len(self.movie_ids)

            # Build dense interaction matrix
            R = np.zeros((n_users, n_movies), dtype=np.float32)
            for _, row in df.iterrows():
                u_idx = self.user_to_idx[int(row["user_id"])]
                m_idx = self.movie_to_idx[int(row["movie_id"])]
                R[u_idx, m_idx] = float(row["score"])

            self.user_item_matrix = R

            # Compute Item-Item cosine similarity matrix (with item centering)
            # Transpose so rows are items, columns are users
            item_matrix = R.T
            self.item_similarity_matrix = cosine_similarity(item_matrix)

            # Fit SVD Matrix Factorization
            # Center user ratings around user mean for unrated movies
            user_ratings_mean = np.zeros((n_users, 1), dtype=np.float32)
            for u in range(n_users):
                rated_indices = R[u] > 0
                if np.any(rated_indices):
                    user_ratings_mean[u] = np.mean(R[u, rated_indices])
                else:
                    user_ratings_mean[u] = 7.0

            # Demeaned matrix for SVD
            R_demeaned = np.zeros_like(R)
            for u in range(n_users):
                rated_indices = R[u] > 0
                R_demeaned[u, rated_indices] = R[u, rated_indices] - user_ratings_mean[u]

            # Choose optimal k for SVD
            k = min(self.n_factors, min(n_users, n_movies) - 1)
            if k >= 1:
                U, sigma, Vt = svds(R_demeaned, k=k)
                sigma_diag = np.diag(sigma)
                predicted_demeaned = np.dot(np.dot(U, sigma_diag), Vt)
                self.predicted_ratings_matrix = predicted_demeaned + user_ratings_mean
            else:
                self.predicted_ratings_matrix = R.copy()

            self.is_trained = True
            logger.info(f"[Collaborative Engine] Successfully trained SVD & Item-Item model ({n_users} users, {n_movies} movies, {self.total_interactions} interactions).")
            return True

        except Exception as e:
            logger.error(f"[Collaborative Engine] Training failed: {e}", exc_info=True)
            self.is_trained = False
            return False

    def get_collaborative_recommendations(
        self,
        user_id: int,
        top_n: int = 15,
        exclude_ids: Optional[Set[int]] = None
    ) -> List[Tuple[int, float, str]]:
        """
        Generates collaborative filtering recommendations for a specific user using
        SVD rating predictions and item-item affinity.
        Returns: List of tuples (movie_id, normalized_score_0_to_1, explanation)
        """
        if not self.is_trained or self.predicted_ratings_matrix is None:
            return []

        if exclude_ids is None:
            exclude_ids = set()

        # If user is in trained matrix
        if user_id in self.user_to_idx:
            u_idx = self.user_to_idx[user_id]
            predictions = self.predicted_ratings_matrix[u_idx]

            # Find movies already rated/interacted by this user
            if self.user_item_matrix is not None:
                interacted_indices = np.where(self.user_item_matrix[u_idx] > 0)[0]
                interacted_ids = {self.idx_to_movie[idx] for idx in interacted_indices}
                exclude_ids = exclude_ids.union(interacted_ids)

            # Sort candidate movies by predicted rating descending
            ranked_indices = np.argsort(predictions)[::-1]
            results: List[Tuple[int, float, str]] = []

            for idx in ranked_indices:
                movie_id = self.idx_to_movie[idx]
                if movie_id in exclude_ids:
                    continue

                pred_score = float(predictions[idx])
                # Normalize predicted score (typically 1-10) to [0, 1] range
                norm_score = max(0.0, min(1.0, pred_score / 10.0))

                explanation = "Highly rated by users with similar cinematic preferences"
                results.append((movie_id, norm_score, explanation))

                if len(results) >= top_n:
                    break

            return results

        return []

    def get_item_collaborative_similar(
        self,
        movie_id: int,
        top_n: int = 8
    ) -> List[Tuple[int, float, str]]:
        """
        Finds movies frequently co-watched or highly rated by the same users.
        """
        if not self.is_trained or self.item_similarity_matrix is None:
            return []

        if movie_id not in self.movie_to_idx:
            return []

        m_idx = self.movie_to_idx[movie_id]
        similarities = self.item_similarity_matrix[m_idx]

        ranked_indices = np.argsort(similarities)[::-1]
        results: List[Tuple[int, float, str]] = []

        for idx in ranked_indices:
            cand_id = self.idx_to_movie[idx]
            if cand_id == movie_id:
                continue

            score = float(similarities[idx])
            if score <= 0.05:
                continue

            explanation = "Frequently co-watched by community members"
            results.append((cand_id, score, explanation))

            if len(results) >= top_n:
                break

        return results

# Singleton instance
collaborative_engine = CollaborativeRecommender()
