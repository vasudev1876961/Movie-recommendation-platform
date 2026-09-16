# scripts/test_phase8.py
import os
import sys
import time

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from fastapi.testclient import TestClient
from backend.app.database.database import SessionLocal
from backend.app.models.movie import Movie
from backend.app.services.trailer_intelligence import trailer_intelligence
from backend.app.services.watch_party_service import watch_party_manager
from backend.app.main import app

def run_phase8_tests():
    print("=" * 80)
    print("MOVIEREC PHASE 8: MULTIMODAL TRAILER INTELLIGENCE & REAL-TIME WATCH PARTIES")
    print("=" * 80)

    db = SessionLocal()
    try:
        # 1. Test Multimodal Trailer Scene Act Segmentation & Telemetry
        print("\n[TEST 1] Testing Multimodal Trailer Scene Act Segmentation & Telemetry Modeling...")
        inception = db.query(Movie).filter(Movie.title.ilike("%Inception%")).first()
        assert inception is not None, "Inception not found in catalog!"

        analysis = trailer_intelligence.analyze_trailer(inception)
        assert analysis.movie_id == inception.id
        assert len(analysis.acts) == 4, f"Expected 4 acts, found {len(analysis.acts)}"
        print(f"✅ Trailer Scene Segmentation for \"{analysis.movie_title}\" (Duration: {analysis.formatted_duration}):")
        for act in analysis.acts:
            print(f"   • {act.act_name} [{act.start_timecode} - {act.end_timecode}] | Mood: {act.dominant_mood} | Velocity: {act.shot_velocity:.1f} cuts/min")
        
        assert len(analysis.telemetry) > 20, f"Expected >20 telemetry samples, got {len(analysis.telemetry)}"
        peak_tension = max(p.tension for p in analysis.telemetry)
        peak_velocity = max(p.shot_velocity for p in analysis.telemetry)
        print(f"✅ Telemetry Samples: {len(analysis.telemetry)} points | Peak Tension: {peak_tension:.1f}% | Peak Velocity: {peak_velocity:.1f} cuts/min")

        # 2. Test Aesthetic DNA & Harmonic Color Palette Extraction
        print("\n[TEST 2] Testing Aesthetic DNA & Harmonic Color Palette Extraction...")
        dna = analysis.aesthetic_dna
        assert len(dna.color_palette) == 5, f"Expected 5-color palette, got {len(dna.color_palette)}"
        palette_summary = ", ".join([f"{c.name} ({c.hex})" for c in dna.color_palette])
        print(f"✅ Aesthetic DNA:")
        print(f"   • Aspect Ratio:   {dna.aspect_ratio}")
        print(f"   • Camera Motion:  {dna.camera_style}")
        print(f"   • Lighting Key:   {dna.lighting_key}")
        print(f"   • Color Palette:  {palette_summary}")
        print(f"   • Spoiler Safety: {dna.spoiler_risk_rating}")

        # 3. Test Multimodal Sensory Trailer Twins Discovery
        print("\n[TEST 3] Testing Multimodal Sensory Trailer Twins Discovery...")
        twins_resp = trailer_intelligence.find_sensory_twins(inception.id, db=db, limit=4)
        assert len(twins_resp.twins) > 0, "Expected at least 1 sensory twin trailer"
        print(f"✅ Sensory Twins for \"{inception.title}\":")
        for twin in twins_resp.twins:
            print(f"   • {twin.title} ({twin.year}) — Cadence Match: {twin.sensory_similarity_score:.1f}% | Pacing: {twin.matching_pacing}")

        # 4. Test Watch Party Room Creation & Lifecycle
        print("\n[TEST 4] Testing Watch Party Room Creation & State Management...")
        room = watch_party_manager.create_room(
            movie_id=inception.id,
            movie_title=inception.title,
            poster_path=inception.poster_path or "",
            trailer_key=inception.trailer or "YoHD9XEInc0",
            host_nickname="VisionaryHost",
            room_title="Inception 70mm Sync Party",
            is_public=True,
            host_only_control=False
        )
        assert room.room_code.startswith("CINE-")
        print(f"✅ Watch Party Created:")
        print(f"   • Room Code: {room.room_code}")
        print(f"   • Host:      {room.host_nickname} (ID: {room.host_id})")
        print(f"   • Title:     {room.room_title}")

        # Test Participant Join
        part = watch_party_manager.join_participant(room.room_code, "guest_99", "Cinephile99")
        assert part is not None
        assert part.role == "viewer"
        print(f"✅ Guest joined: {part.nickname} ({part.role})")

        # 5. Test Collaborative Up-Next Queue & Voting
        print("\n[TEST 5] Testing Collaborative Up-Next Queue & Real-Time Voting...")
        dark_knight = db.query(Movie).filter(Movie.title.ilike("%The Dark Knight%")).first()
        interstellar = db.query(Movie).filter(Movie.title.ilike("%Interstellar%")).first()

        item1 = watch_party_manager.add_to_queue(
            room_code=room.room_code,
            movie_id=dark_knight.id,
            title=dark_knight.title,
            poster_path=dark_knight.poster_path or "",
            rating=dark_knight.rating or 9.0,
            year="2008",
            trailer_key="EXeTwQWrcwY",
            queued_by="Cinephile99",
            client_id="guest_99"
        )
        assert item1.votes == 1

        if interstellar:
            item2 = watch_party_manager.add_to_queue(
                room_code=room.room_code,
                movie_id=interstellar.id,
                title=interstellar.title,
                poster_path=interstellar.poster_path or "",
                rating=interstellar.rating or 8.7,
                year="2014",
                trailer_key="zSWdZVtXT7E",
                queued_by="VisionaryHost",
                client_id=room.host_id
            )
            # Host upvotes dark knight
            watch_party_manager.vote_queue_item(room.room_code, item1.queue_id, room.host_id, vote_delta=1)

        state = watch_party_manager.get_room(room.room_code)
        assert len(state.queue) >= 1
        print(f"✅ Up-Next Queue ({len(state.queue)} items):")
        for q in state.queue:
            print(f"   • #{q.title} — {q.votes} votes (Queued by {q.queued_by})")
        assert state.queue[0].title == dark_knight.title, "Dark Knight should be top voted"

        # 6. Test AI CineBot Trivia Generation
        print("\n[TEST 6] Testing AI CineBot Contextual Scene Trivia...")
        trivia_msg = watch_party_manager.generate_ai_trivia(room.room_code, inception.title, current_time=45.0)
        assert trivia_msg.is_ai is True
        print(f"✅ AI CineBot Trivia: \"{trivia_msg.text}\"")

        # 7. Test FastAPI REST Endpoints via TestClient
        print("\n[TEST 7] Testing FastAPI REST Endpoints via TestClient...")
        client = TestClient(app)

        # 7a. GET /api/trailers/{id}/analysis
        res = client.get(f"/api/trailers/{inception.id}/analysis")
        assert res.status_code == 200, f"Analysis failed: {res.text}"
        a_data = res.json()
        assert a_data["movie_id"] == inception.id
        assert len(a_data["acts"]) == 4
        print(f"✅ GET /api/trailers/{inception.id}/analysis -> 200 OK (4 acts, {len(a_data['telemetry'])} samples)")

        # 7b. GET /api/trailers/{id}/twins
        res = client.get(f"/api/trailers/{inception.id}/twins?limit=3")
        assert res.status_code == 200, f"Twins failed: {res.text}"
        t_data = res.json()
        assert len(t_data["twins"]) > 0
        print(f"✅ GET /api/trailers/{inception.id}/twins -> 200 OK ({len(t_data['twins'])} sensory twins)")

        # 7c. POST /api/trailers/vibe-search
        res = client.post("/api/trailers/vibe-search", json={
            "min_tension": 40.0,
            "min_adrenaline": 10.0,
            "limit": 5
        })
        assert res.status_code == 200
        v_data = res.json()
        assert len(v_data) > 0, "Expected at least 1 vibe matching trailer"
        print(f"✅ POST /api/trailers/vibe-search -> 200 OK ({len(v_data)} matching trailers: {', '.join([v['title'] for v in v_data[:3]])})")

        # 7d. POST /api/watch-party/create
        res = client.post("/api/watch-party/create", json={
            "movie_id": inception.id,
            "room_title": "Automated Test Cinema",
            "host_nickname": "TestBot",
            "is_public": True,
            "host_only_control": False
        })
        assert res.status_code == 200
        c_room = res.json()
        test_code = c_room["room_code"]
        print(f"✅ POST /api/watch-party/create -> 200 OK (Room: {test_code})")

        # 7e. GET /api/watch-party/rooms
        res = client.get("/api/watch-party/rooms")
        assert res.status_code == 200
        rooms_list = res.json()
        assert len(rooms_list) >= 1
        print(f"✅ GET /api/watch-party/rooms -> 200 OK ({len(rooms_list)} public rooms)")

        # 7f. GET /api/watch-party/{room_code}
        res = client.get(f"/api/watch-party/{test_code}")
        assert res.status_code == 200
        r_state = res.json()
        assert r_state["room"]["room_code"] == test_code
        print(f"✅ GET /api/watch-party/{test_code} -> 200 OK ({r_state['room']['room_title']})")

        # 7g. POST /api/watch-party/{room_code}/trivia
        res = client.post(f"/api/watch-party/{test_code}/trivia?current_time=30.0")
        assert res.status_code == 200
        triv_data = res.json()
        assert triv_data["is_ai"] is True
        print(f"✅ POST /api/watch-party/{test_code}/trivia -> 200 OK")

        # 8. Test WebSocket Real-Time Playback Synchronization & Reactions
        print("\n[TEST 8] Testing WebSocket Real-Time Synchronization & Reaction Emotes...")
        with client.websocket_connect(f"/api/watch-party/ws/{test_code}?client_id=ws_host&nickname=HostWS") as ws1:
            welcome = ws1.receive_json()
            assert welcome["action"] == "USER_JOINED"
            print(f"✅ WebSocket Client 1 connected: Action: {welcome['action']}")

            # Connect Client 2
            with client.websocket_connect(f"/api/watch-party/ws/{test_code}?client_id=ws_guest&nickname=GuestWS") as ws2:
                # ws1 and ws2 receive USER_JOINED for client 2
                join_msg1 = ws1.receive_json()
                assert join_msg1["action"] == "USER_JOINED"
                assert join_msg1["nickname"] == "GuestWS"

                join_msg2 = ws2.receive_json()
                assert join_msg2["action"] == "USER_JOINED"
                assert join_msg2["nickname"] == "GuestWS"
                print(f"✅ WebSocket Client 2 presence broadcasted to Room")

                # Test SYNC_PLAY
                ws1.send_json({
                    "action": "SYNC_PLAY",
                    "payload": { "timestamp": 12.5 }
                })
                sync_msg = ws2.receive_json()
                assert sync_msg["action"] == "SYNC_PLAY"
                assert sync_msg["payload"]["current_time"] == 12.5
                print(f"✅ SYNC_PLAY broadcasted from Host to Guest: timestamp {sync_msg['payload']['current_time']}s")

                # Test SEND_REACTION
                ws2.send_json({
                    "action": "SEND_REACTION",
                    "payload": { "emoji": "🔥" }
                })
                rx_msg = ws1.receive_json()
                assert rx_msg["action"] == "RECEIVE_REACTION"
                assert rx_msg["emoji"] == "🔥"
                print(f"✅ SEND_REACTION '🔥' broadcasted from Guest to Host in real-time")

                # Test SEND_CHAT
                ws2.send_json({
                    "action": "SEND_CHAT",
                    "payload": { "text": "This trailer looks stunning in 4K!" }
                })
                chat_msg = ws1.receive_json()
                assert chat_msg["action"] == "RECEIVE_CHAT"
                assert "stunning" in chat_msg["message"]["text"]
                print(f"✅ SEND_CHAT message received by Host: \"{chat_msg['message']['text']}\"")

        print("\n" + "=" * 80)
        print("🎉 ALL PHASE 8 MULTIMODAL TRAILER & WATCH PARTY TESTS PASSED PERFECTLY!")
        print("=" * 80)

    finally:
        db.close()

if __name__ == "__main__":
    run_phase8_tests()
