# scripts/test_phase7.py
import os
import sys

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from fastapi.testclient import TestClient
from backend.app.database.database import SessionLocal
from backend.app.models.movie import Movie
from backend.app.services.streaming_resolver import streaming_resolver
from backend.app.services.chat.chat_session import chat_session_manager
from backend.app.services.chat.chat_engine import cine_copilot
from backend.app.main import app

def run_phase7_tests():
    print("=" * 80)
    print("MOVIEREC PHASE 7: CONVERSATIONAL AI COPILOT & STREAMING PROVIDERS RESOLVER")
    print("=" * 80)

    db = SessionLocal()
    try:
        # 1. Test Streaming Service Providers Registry
        print("\n[TEST 1] Testing Streaming Service Providers Registry & Metadata...")
        providers = streaming_resolver.list_all_providers(region="US", db=db)
        assert len(providers) >= 10, f"Expected at least 10 providers, found {len(providers)}"
        p_names = [p.name for p in providers]
        print(f"✅ Found {len(providers)} Active Streaming Platforms:")
        print(f"   Providers: {', '.join(p_names)}")
        assert any(p.provider_id == "netflix" for p in providers), "Netflix missing from registry"
        assert any(p.provider_id == "prime" for p in providers), "Prime missing from registry"
        assert any(p.provider_id == "max" for p in providers), "Max missing from registry"
        assert any(p.provider_id == "disney" for p in providers), "Disney+ missing from registry"
        assert any(p.provider_id == "apple" for p in providers), "Apple TV+ missing from registry"

        # 2. Test Movie Watch Availability Resolution
        print("\n[TEST 2] Testing Movie Watch Availability Resolution for Catalog Titles...")
        inception = db.query(Movie).filter(Movie.title.ilike("%Inception%")).first()
        assert inception is not None, "Inception not found in catalog!"

        avail = streaming_resolver.resolve_movie_availability(inception, region="US")
        assert avail.movie_id == inception.id
        assert len(avail.stream) > 0, "Expected subscription stream options for Inception"
        assert len(avail.rent) > 0, "Expected rental options for Inception"
        assert len(avail.buy) > 0, "Expected purchase options for Inception"

        stream_plat = ", ".join([f"{o.provider.name} ({o.quality})" for o in avail.stream])
        rent_plat = ", ".join([f"{o.provider.name} ({o.price})" for o in avail.rent[:2]])
        print(f"✅ Watch Availability for \"{inception.title}\" (Region: {avail.region}):")
        print(f"   Stream: {stream_plat}")
        print(f"   Rent:   {rent_plat}")
        print(f"   Deep Link Sample: {avail.stream[0].deep_link}")

        # 3. Test Provider Catalog Filtering
        print("\n[TEST 3] Testing Provider Catalog Filtering...")
        netflix_movies = streaming_resolver.get_movies_by_provider("netflix", region="US", db=db)
        max_movies = streaming_resolver.get_movies_by_provider("max", region="US", db=db)
        print(f"✅ Found {len(netflix_movies)} movies available on Netflix: {', '.join([m.title for m in netflix_movies[:4]])}...")
        print(f"✅ Found {len(max_movies)} movies available on Max: {', '.join([m.title for m in max_movies[:4]])}...")
        assert len(netflix_movies) > 0, "Expected movies on Netflix"
        assert len(max_movies) > 0, "Expected movies on Max"

        # 4. Test Chat Session Memory & Coreference Resolution
        print("\n[TEST 4] Testing Chat Session Memory & Coreference Resolution...")
        session = chat_session_manager.get_or_create("test_session_phase7")
        assert session.session_id == "test_session_phase7"

        # Simulate first turn recommendations
        interstellar = db.query(Movie).filter(Movie.title.ilike("%Interstellar%")).first()
        from backend.app.api.movies import format_movie_list_item
        session.active_movie_pool = [
            format_movie_list_item(inception),
            format_movie_list_item(interstellar) if interstellar else format_movie_list_item(inception)
        ]

        # Test ordinal reference resolution
        ref1 = session.get_referenced_movie("Where can I stream the first one?")
        assert ref1 is not None and ref1.title == inception.title, f"Expected Inception, got {ref1.title if ref1 else None}"
        print(f"✅ Coreference 'the first one' successfully resolved to: \"{ref1.title}\"")

        if interstellar:
            ref2 = session.get_referenced_movie("Tell me more about the second film")
            assert ref2 is not None and ref2.title == interstellar.title
            print(f"✅ Coreference 'the second film' successfully resolved to: \"{ref2.title}\"")

        # 5. Test CineCopilot Multi-Turn Conversational Intent Routing
        print("\n[TEST 5] Testing CineCopilot Conversational Tool Orchestration...")
        # 5a. Recommendation query
        r1 = cine_copilot.process_message(
            message="Recommend mind-bending sci-fi movies where time collapses",
            session_id="test_session_phase7",
            db=db
        )
        assert r1.intent == "RECOMMEND"
        assert len(r1.movies) > 0
        assert len(r1.tools_invoked) > 0
        print(f"✅ Turn 1 (Intent: {r1.intent}): Returned {len(r1.movies)} movies with streaming options.")
        print(f"   Tools: {', '.join([t.tool_name for t in r1.tools_invoked])}")
        print(f"   Followups: {r1.suggested_followups[:2]}")

        # 5b. Streaming query with coreference
        r2 = cine_copilot.process_message(
            message="Where can I stream the first one?",
            session_id="test_session_phase7",
            db=db
        )
        assert r2.intent == "STREAMING_LOOKUP"
        assert len(r2.movies) == 1
        assert r2.movies[0].id in r2.streaming_options
        print(f"✅ Turn 2 (Intent: {r2.intent}): Resolved \"{r2.movies[0].title}\" with streaming guide.")
        print(f"   Reply snippet: {r2.reply.splitlines()[0]}")

        # 5c. Film comparison query
        r3 = cine_copilot.process_message(
            message="Compare Inception vs Interstellar",
            session_id="test_session_phase7",
            db=db
        )
        assert r3.intent == "FILM_COMPARISON"
        assert len(r3.movies) == 2
        print(f"✅ Turn 3 (Intent: {r3.intent}): Side-by-side comparison of 2 films executed.")

        # 5d. Critic debate query
        r4 = cine_copilot.process_message(
            message="What do critics think of Inception?",
            session_id="test_session_phase7",
            db=db
        )
        assert r4.intent == "CRITIC_DEBATE"
        print(f"✅ Turn 4 (Intent: {r4.intent}): Critic Rubric & Arbiter Consensus extracted.")

        # 5e. Knowledge graph director query
        r5 = cine_copilot.process_message(
            message="Show movies directed by Christopher Nolan",
            session_id="test_session_phase7",
            db=db
        )
        assert r5.intent == "KNOWLEDGE_GRAPH"
        print(f"✅ Turn 5 (Intent: {r5.intent}): Knowledge Graph traversed for Christopher Nolan.")

        # 6. Test FastAPI REST Endpoints via TestClient
        print("\n[TEST 6] Testing FastAPI Phase 7 Streaming & Chat Endpoints...")
        client = TestClient(app)

        # 6a. GET /api/streaming/providers
        res = client.get("/api/streaming/providers?region=US")
        assert res.status_code == 200, f"GET providers failed: {res.text}"
        data = res.json()
        assert data["total_providers"] >= 10
        print(f"✅ GET /api/streaming/providers -> 200 OK ({data['total_providers']} providers)")

        # 6b. GET /api/streaming/movie/{id}
        res = client.get(f"/api/streaming/movie/{inception.id}?region=US")
        assert res.status_code == 200, f"GET movie streaming failed: {res.text}"
        m_data = res.json()
        assert len(m_data["stream"]) > 0
        print(f"✅ GET /api/streaming/movie/{inception.id} -> 200 OK (Stream on {m_data['stream'][0]['provider']['name']})")

        # 6c. GET /api/streaming/browse
        res = client.get("/api/streaming/browse?provider=netflix&region=US")
        assert res.status_code == 200, f"GET browse failed: {res.text}"
        b_data = res.json()
        assert b_data["total"] > 0
        print(f"✅ GET /api/streaming/browse?provider=netflix -> 200 OK ({b_data['total']} titles)")

        # 6d. GET /api/chat/starters
        res = client.get("/api/chat/starters")
        assert res.status_code == 200, f"GET starters failed: {res.text}"
        s_data = res.json()
        assert len(s_data["starters"]) >= 4
        print(f"✅ GET /api/chat/starters -> 200 OK ({len(s_data['starters'])} starter prompts)")

        # 6e. POST /api/chat/message
        res = client.post("/api/chat/message", json={
            "message": "Where can I watch The Dark Knight?",
            "region": "US"
        })
        assert res.status_code == 200, f"POST chat failed: {res.text}"
        c_data = res.json()
        assert c_data["intent"] == "STREAMING_LOOKUP"
        assert len(c_data["movies"]) > 0
        print(f"✅ POST /api/chat/message -> 200 OK (Intent: {c_data['intent']}, Movies: {len(c_data['movies'])})")

        # 6f. GET /api/chat/history/{session_id}
        res = client.get(f"/api/chat/history/{c_data['session_id']}")
        assert res.status_code == 200
        h_data = res.json()
        assert h_data["total_messages"] >= 2
        print(f"✅ GET /api/chat/history -> 200 OK ({h_data['total_messages']} turns recorded)")

        # 6g. DELETE /api/chat/session/{session_id}
        res = client.delete(f"/api/chat/session/{c_data['session_id']}")
        assert res.status_code == 200
        del_data = res.json()
        assert del_data["cleared"] is True
        print(f"✅ DELETE /api/chat/session -> 200 OK (Session memory cleared)")

        print("\n" + "=" * 80)
        print("🎉 ALL PHASE 7 STREAMING & CINECOPILOT TESTS PASSED PERFECTLY!")
        print("=" * 80)

    finally:
        db.close()

if __name__ == "__main__":
    run_phase7_tests()
