# backend/app/services/semantic_search.py
import os
import re
import pickle
import logging
from typing import List, Dict, Tuple, Optional, Set
import numpy as np
from sqlalchemy.orm import Session
from backend.app.models.movie import Movie

logger = logging.getLogger("movie_app")

CACHE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "movie_embeddings.pkl")

class SemanticSearchEngine:
    """
    Neural Semantic Search & Vector Discovery Engine powered by SentenceTransformers (all-MiniLM-L6-v2).
    Generates 384-dimensional dense vector embeddings for movies and natural language queries,
    performing real-time sub-millisecond cosine similarity matrix operations.
    """

    MODEL_NAME = "all-MiniLM-L6-v2"

    def __init__(self):
        self.model = None
        self.embedding_matrix: Optional[np.ndarray] = None  # Shape: (N, 384)
        self.movie_ids: List[int] = []
        self.movie_id_to_idx: Dict[int, int] = {}
        self.idx_to_movie_id: Dict[int, int] = {}
        self.movie_metadata: Dict[int, dict] = {}
        self.is_trained: bool = False
        self._model_loaded: bool = False

    def _ensure_model_loaded(self):
        """Lazy loads the SentenceTransformer model into memory."""
        if self._model_loaded and self.model is not None:
            return

        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"[Semantic Search Engine] Loading neural model '{self.MODEL_NAME}'...")
            self.model = SentenceTransformer(self.MODEL_NAME)
            self._model_loaded = True
            logger.info(f"[Semantic Search Engine] Neural model '{self.MODEL_NAME}' loaded successfully.")
        except Exception as e:
            logger.error(f"[Semantic Search Engine] Failed to load SentenceTransformer: {e}", exc_info=True)
            self._model_loaded = False
            self.model = None

    def _build_semantic_document(self, movie: Movie) -> str:
        """
        Constructs a cohesive, natural language descriptive narrative for the movie
        optimized for dense neural transformer attention.
        """
        title = (movie.title or "").strip()
        overview = (movie.overview or "").strip()
        tagline = (movie.tagline or "").strip()
        keywords = (movie.keywords or "").replace(",", " ").strip()
        mood = (movie.mood or "").replace(",", " ").strip()

        genres = [g.name for g in movie.genres if g.name]
        genres_str = ", ".join(genres) if genres else "Cinema"

        directors = [d.name for d in movie.directors if d.name]
        directors_str = f"Directed by {', '.join(directors)}." if directors else ""

        cast = [
            assoc.cast_member.name
            for assoc in sorted(movie.cast_associations, key=lambda x: x.cast_order)[:4]
            if assoc.cast_member and assoc.cast_member.name
        ]
        cast_str = f"Starring {', '.join(cast)}." if cast else ""

        doc_parts = [
            f"Title: {title}.",
            f"Genre: {genres_str}." if genres_str else "",
            f"Tagline: \"{tagline}\"." if tagline else "",
            f"Synopsis: {overview}" if overview else "",
            f"Themes, Mood and Style: {mood} {keywords}." if (mood or keywords) else "",
            directors_str,
            cast_str
        ]

        full_doc = " ".join(p for p in doc_parts if p)
        return re.sub(r'\s+', ' ', full_doc).strip()

    def fit(self, db: Session, force_recompute: bool = False) -> bool:
        """
        Generates or loads cached dense vector embeddings for all movies in the database.
        Embeddings are L2-normalized so dot products equal cosine similarities.
        """
        try:
            movies: List[Movie] = db.query(Movie).all()
            if not movies:
                logger.warning("[Semantic Search Engine] No movies found in database to index.")
                return False

            self.movie_ids = []
            self.movie_id_to_idx = {}
            self.idx_to_movie_id = {}
            self.movie_metadata = {}
            documents = []

            for idx, movie in enumerate(movies):
                self.movie_ids.append(movie.id)
                self.movie_id_to_idx[movie.id] = idx
                self.idx_to_movie_id[idx] = movie.id

                # Cache lightweight metadata for fast reason generation & filtering
                self.movie_metadata[movie.id] = {
                    "id": movie.id,
                    "title": movie.title,
                    "rating": movie.rating,
                    "popularity": movie.popularity,
                    "overview": movie.overview or "",
                    "tagline": movie.tagline or "",
                    "mood": movie.mood or "",
                    "keywords": movie.keywords or "",
                    "genres": [g.name for g in movie.genres],
                    "directors": [d.name for d in movie.directors],
                    "cast": [assoc.cast_member.name for assoc in movie.cast_associations[:4] if assoc.cast_member]
                }

                doc = self._build_semantic_document(movie)
                documents.append(doc)

            # Check if cached embeddings match current movie count and IDs
            cache_valid = False
            if not force_recompute and os.path.exists(CACHE_PATH):
                try:
                    with open(CACHE_PATH, "rb") as f:
                        cached_data = pickle.load(f)
                    if cached_data.get("movie_ids") == self.movie_ids and cached_data.get("embeddings") is not None:
                        self.embedding_matrix = cached_data["embeddings"]
                        cache_valid = True
                        logger.info(f"[Semantic Search Engine] Loaded {len(self.movie_ids)} cached neural embeddings from disk.")
                except Exception as e:
                    logger.warning(f"[Semantic Search Engine] Could not load embedding cache: {e}")

            if not cache_valid:
                self._ensure_model_loaded()
                if self.model is None:
                    raise RuntimeError("SentenceTransformer model could not be loaded.")

                logger.info(f"[Semantic Search Engine] Computing neural embeddings for {len(documents)} movies with '{self.MODEL_NAME}'...")
                # Compute dense embeddings
                embeddings = self.model.encode(
                    documents,
                    batch_size=32,
                    show_progress_bar=False,
                    convert_to_numpy=True,
                    normalize_embeddings=True
                )
                self.embedding_matrix = embeddings.astype(np.float32)

                # Persist cache to disk
                try:
                    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
                    with open(CACHE_PATH, "wb") as f:
                        pickle.dump({
                            "movie_ids": self.movie_ids,
                            "embeddings": self.embedding_matrix
                        }, f)
                    logger.info(f"[Semantic Search Engine] Successfully cached neural embeddings to '{CACHE_PATH}'.")
                except Exception as e:
                    logger.warning(f"[Semantic Search Engine] Failed to write cache to disk: {e}")

            self.is_trained = True
            logger.info(f"[Semantic Search Engine] Indexing complete: {self.embedding_matrix.shape[0]} movies indexed (dim={self.embedding_matrix.shape[1]}).")
            return True

        except Exception as e:
            logger.error(f"[Semantic Search Engine] Embedding indexing failed: {e}", exc_info=True)
            self.is_trained = False
            return False

    def search(
        self,
        query: str,
        top_k: int = 12,
        min_score: float = 0.15,
        genre_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        Executes a dense neural semantic search for natural language prompts.
        Returns top-k matching movies with cosine similarity scores, match percentages, and thematic reasoning.
        """
        query_text = (query or "").strip()
        if not query_text or not self.is_trained or self.embedding_matrix is None:
            return []

        self._ensure_model_loaded()
        if self.model is None:
            return []

        # Generate normalized query embedding
        query_vec = self.model.encode(
            query_text,
            convert_to_numpy=True,
            normalize_embeddings=True
        ).astype(np.float32)

        # Dot product with all normalized movie embeddings gives cosine similarity (-1.0 to 1.0)
        cosine_scores = np.dot(self.embedding_matrix, query_vec)

        # Lexical exact match boost for titles/directors/cast to provide hybrid strength
        q_lower = query_text.lower()
        q_tokens = set(re.findall(r'\b\w+\b', q_lower))

        scored_candidates = []
        for idx, base_score in enumerate(cosine_scores):
            movie_id = self.idx_to_movie_id[idx]
            meta = self.movie_metadata.get(movie_id, {})

            # Apply genre filter if specified
            if genre_filter and genre_filter.lower() != "all":
                movie_genres = [g.lower() for g in meta.get("genres", [])]
                if genre_filter.lower() not in movie_genres:
                    continue

            # Hybrid token bonus
            bonus = 0.0
            m_title = meta.get("title", "").lower()
            if q_lower in m_title:
                bonus += 0.15
            elif any(t in m_title.split() for t in q_tokens if len(t) > 3):
                bonus += 0.08

            directors = [d.lower() for d in meta.get("directors", [])]
            if any(d in q_lower for d in directors):
                bonus += 0.12

            final_score = float(base_score) + bonus
            if final_score >= min_score:
                scored_candidates.append((movie_id, float(base_score), final_score, meta))

        # Sort by final score descending
        scored_candidates.sort(key=lambda x: x[2], reverse=True)
        top_candidates = scored_candidates[:top_k]

        results = []
        for movie_id, raw_cosine, final_score, meta in top_candidates:
            # Calibrate cosine similarity (typically 0.20-0.75) to intuitive user match % (65% - 99%)
            match_pct = min(99.0, max(65.0, round(50.0 + (raw_cosine * 60.0), 1)))

            reasoning = self._generate_thematic_reasoning(query_text, meta, raw_cosine)

            results.append({
                "movie_id": movie_id,
                "cosine_similarity": round(float(raw_cosine), 4),
                "match_score": match_pct,
                "reasoning": reasoning,
                "thematic_tags": meta.get("genres", []) + ([meta.get("mood", "")] if meta.get("mood") else [])
            })

        return results

    def get_conceptual_twins(
        self,
        movie_id: int,
        top_n: int = 6,
        min_similarity: float = 0.25
    ) -> List[Tuple[int, float, str]]:
        """
        Discovers conceptually and thematically twin movies via nearest neighbors
        in dense embedding space.
        Returns: List of tuples (movie_id, similarity_score_0_to_1, explanation_reason)
        """
        if not self.is_trained or self.embedding_matrix is None:
            return []

        if movie_id not in self.movie_id_to_idx:
            return []

        target_idx = self.movie_id_to_idx[movie_id]
        target_vec = self.embedding_matrix[target_idx]

        # Compute cosine similarity
        similarities = np.dot(self.embedding_matrix, target_vec)

        ranked_indices = np.argsort(similarities)[::-1]
        results = []
        target_meta = self.movie_metadata.get(movie_id, {})

        for idx in ranked_indices:
            candidate_id = self.idx_to_movie_id[idx]
            if candidate_id == movie_id:
                continue

            score = float(similarities[idx])
            if score < min_similarity:
                continue

            cand_meta = self.movie_metadata.get(candidate_id, {})

            # Generate conceptual twin explanation
            common_genres = set(target_meta.get("genres", [])).intersection(set(cand_meta.get("genres", [])))
            target_mood = target_meta.get("mood", "")
            cand_mood = cand_meta.get("mood", "")

            reasons = []
            if target_mood and cand_mood and target_mood.lower() == cand_mood.lower():
                reasons.append(f"Shared {target_mood.lower()} atmosphere")
            if common_genres:
                reasons.append(f"Conceptual synergy in {', '.join(list(common_genres)[:2])}")
            if not reasons:
                reasons.append(f"Deep narrative & thematic twin ({round(score*100, 1)}% semantic resonance)")

            explanation = " • ".join(reasons)
            results.append((candidate_id, score, explanation))

            if len(results) >= top_n:
                break

        return results

    def _generate_thematic_reasoning(self, query: str, meta: dict, cosine_score: float) -> str:
        """Generates dynamic, human-interpretable reasons for why a movie semantically matched."""
        q_tokens = set(re.findall(r'\b[a-zA-Z0-9\-]+\b', query.lower()))
        title = meta.get("title", "")
        overview = meta.get("overview", "").lower()
        genres = meta.get("genres", [])
        keywords = meta.get("keywords", "").lower()
        mood = meta.get("mood", "")
        directors = meta.get("directors", [])
        cast = meta.get("cast", [])

        reasons = []

        # Check for director match
        for d in directors:
            if any(t in d.lower() for t in q_tokens if len(t) > 3):
                reasons.append(f"Vision of director {d}")

        # Check for cast match
        for c in cast:
            if any(t in c.lower() for t in q_tokens if len(t) > 3):
                reasons.append(f"Features {c}")

        # Check for mood/theme alignment
        if mood and mood.lower() in query.lower():
            reasons.append(f"Captures {mood} aesthetic")

        # Check for keyword overlap
        matched_kw = [w for w in q_tokens if len(w) > 3 and (w in keywords or w in overview)]
        if matched_kw:
            reasons.append(f"Aligns with themes: {', '.join(matched_kw[:2])}")

        # Genre harmony
        matched_g = [g for g in genres if g.lower() in query.lower()]
        if matched_g:
            reasons.append(f"Hallmark {matched_g[0]} narrative")

        if not reasons:
            if genres:
                reasons.append(f"Neural match in {genres[0]} cinematic space ({round(cosine_score*100, 1)}% resonance)")
            else:
                reasons.append(f"Strong semantic conceptual resonance ({round(cosine_score*100, 1)}%)")

        return " • ".join(reasons[:2])

# Singleton instance
semantic_search_engine = SemanticSearchEngine()
