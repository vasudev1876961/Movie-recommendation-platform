# scripts/test_phase4.py
import os
import sys

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import numpy as np
from fastapi.testclient import TestClient
from backend.app.database.database import SessionLocal
from backend.app.models.movie import Movie
from backend.app.services.semantic_search import semantic_search_engine
from backend.app.main import app

def run_phase4_tests():
    print("=" * 80)
    print("MOVIEREC PHASE 4: NEURAL SEMANTIC SEARCH & VECTOR EMBEDDINGS TEST SUITE")
    print("=" * 80)

    db = SessionLocal()
    try:
        # 1. Test Semantic Search Engine Initialization & Embeddings
        print("\n[TEST 1] Testing Semantic Search Engine Vector Indexing & Caching...")
        fit_ok = semantic_search_engine.fit(db, force_recompute=True)
        assert fit_ok, "SemanticSearchEngine failed to fit!"
        assert semantic_search_engine.embedding_matrix is not None, "Embedding matrix is None!"
        
        n_movies, dim = semantic_search_engine.embedding_matrix.shape
        print(f"✅ Embedding Matrix Shape: {n_movies} movies x {dim} dimensions (Model: {semantic_search_engine.MODEL_NAME})")
        assert dim == 384, f"Expected 384 dimensions from all-MiniLM-L6-v2, got {dim}"

        # Verify unit normalization
        norms = np.linalg.norm(semantic_search_engine.embedding_matrix, axis=1)
        assert np.allclose(norms, 1.0, atol=1e-3), "Embeddings are not unit normalized!"
        print("✅ Embeddings L2 unit normalization verified (all ||v|| ≈ 1.0).")

        # 2. Test Conceptual Queries
        print("\n[TEST 2] Testing Conceptual Natural Language Queries (Zero Exact Title Match Testing)...")
        test_queries = [
            ("dreams inside dreams subconscious secret theft", "Inception"),
            ("astronaut space travel wormhole black hole father daughter", "Interstellar"),
            ("poor family infiltrates rich house social class basement", "Parasite"),
            ("detective investigating gruesome seven deadly sins serial killer", "Se7en"),
            ("red pill blue pill simulated reality hacker revolution", "Matrix"),
            ("post apocalyptic desert truck chase war boys furiosa", "Mad Max")
        ]

        for query_text, expected_title_sub in test_queries:
            results = semantic_search_engine.search(query_text, top_k=5)
            assert len(results) > 0, f"No results for query '{query_text}'"
            top_hit = results[0]
            top_meta = semantic_search_engine.movie_metadata.get(top_hit["movie_id"], {})
            top_title = top_meta.get("title", "")
            
            print(f"\nQuery: \"{query_text}\"")
            print(f"  👉 Top 1 Pick: {top_title}")
            print(f"     Cosine Similarity: {top_hit['cosine_similarity']:.4f} | Match Score: {top_hit['match_score']}%")
            print(f"     Reasoning: {top_hit['reasoning']}")

            # Verify expected movie is in top 3 results
            top_3_titles = [
                semantic_search_engine.movie_metadata.get(r["movie_id"], {}).get("title", "")
                for r in results[:3]
            ]
            found = any(expected_title_sub.lower() in t.lower() for t in top_3_titles)
            assert found, f"Expected '{expected_title_sub}' in top 3 results, got {top_3_titles}"
            print(f"  ✅ Verified '{expected_title_sub}' in top picks!")

        # 3. Test Movie-to-Movie Conceptual Twins
        print("\n[TEST 3] Testing Movie-to-Movie Conceptual Twin Vector Similarity...")
        inception = db.query(Movie).filter(Movie.title.ilike("%Inception%")).first()
        if inception:
            twins = semantic_search_engine.get_conceptual_twins(inception.id, top_n=5)
            print(f"\nTop 5 Conceptual Twins for '{inception.title}':")
            for m_id, score, reason in twins:
                m_meta = semantic_search_engine.movie_metadata.get(m_id, {})
                print(f"  • {m_meta.get('title', m_id)} — Cosine: {score:.4f} ({round(score*100, 1)}%) | Reason: {reason}")
            assert len(twins) > 0, "No conceptual twins found for Inception!"

        # 4. Test FastAPI Endpoints via TestClient
        print("\n[TEST 4] Testing FastAPI Semantic Endpoints via TestClient...")
        client = TestClient(app)

        # 4a. POST /api/search/semantic
        payload = {
            "query": "intense space exploration with high stakes",
            "limit": 6,
            "min_score": 0.15
        }
        res = client.post("/api/search/semantic", json=payload)
        assert res.status_code == 200, f"POST /api/search/semantic failed: {res.text}"
        data = res.json()
        assert data["total"] > 0, "Semantic search endpoint returned 0 items!"
        print(f"✅ POST /api/search/semantic -> 200 OK ({data['total']} items returned)")

        # 4b. GET /api/movies/{id}/semantic-similar
        if inception:
            res = client.get(f"/api/movies/{inception.id}/semantic-similar?limit=4")
            assert res.status_code == 200, f"GET /api/movies/{inception.id}/semantic-similar failed: {res.text}"
            twin_data = res.json()
            assert len(twin_data) > 0, "Conceptual twins endpoint returned 0 items!"
            print(f"✅ GET /api/movies/{inception.id}/semantic-similar -> 200 OK ({len(twin_data)} items)")

        # 4c. GET /api/movies/search?q=...&semantic=true
        res = client.get("/api/movies/search?q=space+black+hole&semantic=true&limit=5")
        assert res.status_code == 200, f"GET /api/movies/search with semantic=true failed: {res.text}"
        search_data = res.json()
        assert len(search_data) > 0, "Semantic search query returned 0 items!"
        print(f"✅ GET /api/movies/search?semantic=true -> 200 OK ({len(search_data)} items)")

        # 4d. POST /api/ai/recommend (Phase 4 Neural Upgrade)
        res = client.post("/api/ai/recommend", json={"query": "A mind-bending psychological thriller", "limit": 4})
        assert res.status_code == 200, f"POST /api/ai/recommend failed: {res.text}"
        ai_data = res.json()
        assert len(ai_data["recommendations"]) > 0, "AI recommend returned 0 items!"
        print(f"✅ POST /api/ai/recommend (Neural Upgrade) -> 200 OK ({len(ai_data['recommendations'])} items)")

        # 4e. POST /api/admin/embeddings/reindex
        res = client.post("/api/admin/embeddings/reindex")
        assert res.status_code == 200, f"POST /api/admin/embeddings/reindex failed: {res.text}"
        reindex_data = res.json()
        assert reindex_data["status"] == "success", "Reindex endpoint did not return success!"
        print(f"✅ POST /api/admin/embeddings/reindex -> 200 OK ({reindex_data['message']})")

        print("\n" + "=" * 80)
        print("🎉 ALL PHASE 4 NEURAL SEMANTIC SEARCH TESTS PASSED PERFECTLY!")
        print("=" * 80)

    finally:
        db.close()

if __name__ == "__main__":
    run_phase4_tests()
