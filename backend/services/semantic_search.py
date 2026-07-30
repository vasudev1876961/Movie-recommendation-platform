# backend/services/semantic_search.py
import logging
import math
import asyncio
import httpx
from typing import List, Optional
from backend.config import settings
from backend.database import db
from backend.data.movies import movies as local_movies

logger = logging.getLogger("uvicorn.error")
embeddings_collection = db["movie_embeddings"]

class SemanticSearchService:
    def __init__(self):
        # Public Hugging Face inference API for sentence embeddings
        self.api_url = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2"
        self.client = httpx.AsyncClient(timeout=20.0)

    async def get_embedding(self, text: str) -> Optional[List[float]]:
        headers = {}
        # Optional Hugging Face Token for unlimited requests
        hf_token = getattr(settings, "huggingface_api_key", "")
        if hf_token:
            headers["Authorization"] = f"Bearer {hf_token}"
            
        payload = {"inputs": text, "options": {"wait_for_model": True}}
        
        try:
            response = await self.client.post(self.api_url, headers=headers, json=payload)
            if response.status_code == 200:
                result = response.json()
                # The API returns a list of floats (embedding)
                if isinstance(result, list) and len(result) > 0:
                    if isinstance(result[0], list): # handle nested lists if returned
                        return result[0]
                    return result
            logger.error(f"Hugging Face API error status={response.status_code} detail={response.text}")
            return None
        except Exception as e:
            logger.error(f"Failed to generate embedding from Hugging Face: {e}")
            return None

    # Precompute and cache movie vectors inside MongoDB on startup
    async def initialize_embeddings(self):
        try:
            # Check document count
            count = await embeddings_collection.count_documents({})
            if count >= len(local_movies):
                logger.info(f"[Semantic Search] Movie embeddings are already cached ({count} movies).")
                return

            logger.info(f"[Semantic Search] Initializing movie embeddings cache in MongoDB...")
            
            # Wipe clean just in case of partial initialization
            await embeddings_collection.delete_many({})

            for movie in local_movies:
                # Build rich textual context representing the movie
                movie_text = f"Title: {movie['title']}. Description: {movie['overview']}. Genres: {', '.join(movie['genres'])}. Keywords: {', '.join(movie.get('keywords', []))}"
                
                vector = await self.get_embedding(movie_text)
                if vector:
                    await embeddings_collection.insert_one({
                        "movie_id": movie["id"],
                        "vector": vector
                    })
                    # Pause briefly to prevent rate limits
                    await asyncio.sleep(0.2)
                else:
                    logger.warning(f"[Semantic Search] Failed to compute vector for movie: {movie['title']}. Skipping.")

            new_count = await embeddings_collection.count_documents({})
            logger.info(f"[Semantic Search] Successfully initialized {new_count} movie embeddings in MongoDB.")
        except Exception as e:
            logger.error(f"[Semantic Search] FAILED to initialize vector database: {e}")

    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        dot_product = sum(x * y for x, y in zip(v1, v2))
        magnitude_v1 = math.sqrt(sum(x * x for x in v1))
        magnitude_v2 = math.sqrt(sum(y * y for y in v2))
        if magnitude_v1 == 0 or magnitude_v2 == 0:
            return 0.0
        return dot_product / (magnitude_v1 * magnitude_v2)

    async def search(self, query: str, limit: int = 12) -> Optional[List[dict]]:
        # 1. Fetch query vector
        query_vector = await self.get_embedding(query)
        if not query_vector:
            logger.warning(f"[Semantic Search] Falling back to keyword filter due to embedding failure.")
            return None # Signals caller to fall back to keyword search

        # 2. Retrieve all cached movie vectors from MongoDB
        cursor = embeddings_collection.find()
        cached_vectors = await cursor.to_list(length=1000)
        
        if not cached_vectors:
            logger.warning(f"[Semantic Search] No movie vectors found in database. Initializing.")
            await self.initialize_embeddings()
            cursor = embeddings_collection.find()
            cached_vectors = await cursor.to_list(length=1000)

        # 3. Calculate cosine similarity
        scored_ids = []
        for doc in cached_vectors:
            movie_id = doc["movie_id"]
            db_vector = doc["vector"]
            similarity = self._cosine_similarity(query_vector, db_vector)
            scored_ids.append((movie_id, similarity))

        # Sort descending by similarity
        scored_ids.sort(key=lambda item: item[1], reverse=True)

        # 4. Map similarity values to movie objects
        results = []
        for m_id, sim in scored_ids[:limit]:
            # Filter low similarity results
            if sim < 0.20:
                continue
                
            movie = next((m for m in local_movies if m["id"] == m_id), None)
            if movie:
                # Create a copy and append the semanticMatchScore key
                movie_copy = movie.copy()
                movie_copy["semanticMatchScore"] = sim
                results.append(movie_copy)

        return results

# Instantiate service singleton
semantic_search = SemanticSearchService()
