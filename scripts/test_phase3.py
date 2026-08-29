# scripts/test_phase3.py
import os
import sys

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.app.database.database import SessionLocal
from backend.app.models.movie import Movie
from backend.app.models.user import User
from backend.app.services.tfidf_recommender import tfidf_engine
from backend.app.services.collaborative_recommender import collaborative_engine
from backend.app.services.hybrid_recommender import hybrid_engine
from fastapi.testclient import TestClient
from backend.app.main import app

def run_tests():
    print("=" * 70)
    print("MOVIEREC PHASE 3: HYBRID RECOMMENDATION ENGINE TEST SUITE")
    print("=" * 70)


    db = SessionLocal()
    try:
        # 1. Test TF-IDF Engine
        print("\n[TEST 1] Testing TF-IDF Content-Based Recommender...")
        tfidf_ok = tfidf_engine.fit(db)
        assert tfidf_ok, "TF-IDF Engine failed to fit!"
        assert tfidf_engine.tfidf_matrix is not None, "TF-IDF matrix is None!"
        print(f"✅ TF-IDF Matrix Shape: {tfidf_engine.tfidf_matrix.shape[0]} movies x {tfidf_engine.tfidf_matrix.shape[1]} features")

        # Find Inception or a popular movie
        inception = db.query(Movie).filter(Movie.title.ilike("%Inception%")).first()
        if inception:
            sims = tfidf_engine.get_similar_movies(inception.id, top_n=5)
            print(f"\nTop 5 TF-IDF Similar Movies to '{inception.title}':")
            for m_id, score, reason in sims:
                m = db.query(Movie).filter(Movie.id == m_id).first()
                print(f"  • {m.title if m else m_id} — Match Score: {round(score*100, 1)}% | Reason: {reason}")
            assert len(sims) > 0, "No similar movies returned for Inception!"

        # 2. Test Collaborative Filtering Engine
        print("\n[TEST 2] Testing Collaborative Filtering (SVD + Item-Item)...")
        collab_ok = collaborative_engine.fit(db)
        assert collab_ok, "Collaborative Engine failed to fit!"
        assert collaborative_engine.predicted_ratings_matrix is not None, "Predicted ratings matrix is None!"
        print(f"✅ SVD Factors: {collaborative_engine.n_factors} | Users: {len(collaborative_engine.user_ids)} | Movies: {len(collaborative_engine.movie_ids)}")

        # Test collaborative recs for demo_user (ID: 1)
        demo_user = db.query(User).filter(User.username == "demo_user").first()
        if demo_user:
            collab_recs = collaborative_engine.get_collaborative_recommendations(demo_user.id, top_n=5)
            print(f"\nTop Collaborative Predictions for '{demo_user.username}':")
            for m_id, score, reason in collab_recs:
                m = db.query(Movie).filter(Movie.id == m_id).first()
                print(f"  • {m.title if m else m_id} — Pred Score: {round(score*100, 1)}% | Reason: {reason}")
            assert len(collab_recs) > 0, "No collaborative recommendations returned!"

        # 3. Test Hybrid Engine Combiner
        print("\n[TEST 3] Testing Hybrid Combiner (Dynamic Weights & AI Explanations)...")
        hybrid_recs = hybrid_engine.get_personalized_recommendations(
            user_id=demo_user.id if demo_user else None,
            db=db,
            limit=6
        )
        assert len(hybrid_recs) > 0, "No hybrid recommendations returned!"
        print(f"\nTop Hybrid Recommendations for '{demo_user.username if demo_user else 'Anonymous'}':")
        for rec in hybrid_recs:
            m = rec["movie"]
            print(f"  ⭐ {m.title} [{rec['match_score']}% Match]")
            print(f"     Reasoning: {rec['reasoning']}")
            print(f"     Scores: Hybrid={rec['hybrid_score']:.3f}, Content={rec['content_score']:.3f}, CF={rec['collab_score']:.3f}")

        # 4. Test FastAPI Endpoints via TestClient
        print("\n[TEST 4] Testing FastAPI Endpoints...")
        client = TestClient(app)

        # Content recommendations endpoint
        if inception:
            resp = client.get(f"/api/recommendations/content/{inception.id}?limit=4")
            assert resp.status_code == 200, f"Content endpoint failed: {resp.text}"
            content_data = resp.json()
            assert len(content_data) > 0, "Content endpoint returned empty results!"
            print(f"✅ GET /api/recommendations/content/{inception.id} -> 200 OK ({len(content_data)} items)")

        # Hybrid recommendations endpoint
        resp = client.get("/api/recommendations/hybrid?limit=6")
        assert resp.status_code == 200, f"Hybrid endpoint failed: {resp.text}"
        hybrid_data = resp.json()
        assert len(hybrid_data) > 0, "Hybrid endpoint returned empty results!"
        print(f"✅ GET /api/recommendations/hybrid -> 200 OK ({len(hybrid_data)} items)")

        # Wizard recommendations endpoint
        wizard_payload = {
            "genres": ["Science Fiction", "Action"],
            "mood": "Mind-bending",
            "era": "2010s",
            "minRating": 8.0,
            "runtime": "120-150"
        }
        resp = client.post("/api/recommendations/wizard", json=wizard_payload)
        assert resp.status_code == 200, f"Wizard endpoint failed: {resp.text}"
        wizard_data = resp.json()
        assert len(wizard_data) > 0, "Wizard endpoint returned empty results!"
        print(f"✅ POST /api/recommendations/wizard -> 200 OK ({len(wizard_data)} items)")

        print("\n" + "=" * 70)
        print("🎉 ALL PHASE 3 TESTS PASSED PERFECTLY!")
        print("=" * 70)

    finally:
        db.close()

if __name__ == "__main__":
    run_tests()
