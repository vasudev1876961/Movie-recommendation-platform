# scripts/test_phase10.py
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
from backend.app.services.spatial_biometrics import spatial_biometrics_service
from backend.app.main import app

def run_phase10_tests():
    print("=" * 80)
    print("MOVIEREC PHASE 10: CINESPATIAL AR 3D SPATIAL THEATER & CINEPULSE BIOMETRICS")
    print("=" * 80)

    db = SessionLocal()
    try:
        # 1. Test 3D Spatial Cinema Environments
        print("\n[TEST 1] Testing 3D Spatial Cinema Environments & Optical Parameters...")
        envs = spatial_biometrics_service.get_environments()
        assert len(envs) == 4, f"Expected 4 environments, got {len(envs)}"
        for env in envs:
            assert env.screen_curvature_rad > 0, f"Invalid curvature for {env.env_id}"
            assert env.ambient_light_hex.startswith("#"), f"Invalid ambient hex for {env.env_id}"
            print(f"   • {env.name:32} | Curvature: {env.screen_curvature_rad:.2f} rad | Ambient: {env.ambient_light_hex} | Particles: {env.particles_type}")

        # 2. Test Binaural 3D Audio HRTF Presets
        print("\n[TEST 2] Testing Binaural 3D Spatial Audio & Dolby Atmos 7.1.4 Soundfields...")
        presets = spatial_biometrics_service.get_audio_presets()
        assert len(presets) >= 3, f"Expected at least 3 audio presets, got {len(presets)}"
        for p in presets:
            assert p.hrtf_enabled is True
            assert len(p.virtual_channels) >= 3
            print(f"   • {p.name:38} | Reverb Decay: {p.reverb_decay_sec:.1f}s | Channels: {len(p.virtual_channels)} | Room: {p.room_reverb_type}")

        # 3. Test CinePulse Autonomic Biometrics Telemetry & Stimulus Engine
        print("\n[TEST 3] Testing CinePulse Real-Time Autonomic Telemetry & Stimuli...")
        movie = db.query(Movie).first()
        assert movie is not None, "No movie found in catalog database!"

        stimuli = ["action_rush", "sudden_shock", "chill_calm", "emotional_tears", None]
        for stim in stimuli:
            res = spatial_biometrics_service.simulate_or_sync_biometrics(
                movie_id=movie.id,
                timecode_sec=42.0,
                vitals=None,
                stimulus=stim,
                db=db
            )
            v = res["vitals"]
            label = stim.upper() if stim else "BASELINE TICK"
            print(f"   • [{label:13}] Heart Rate: {v.heart_rate_bpm:5.1f} BPM | HRV: {v.hrv_ms:4.1f}ms | GSR: {v.galvanic_skin_response_us:4.1f}µS | Stress: {v.stress_level:16} | Alert: {res['bio_alert'] or 'None'}")
            assert v.heart_rate_bpm > 40 and v.heart_rate_bpm < 180
            assert v.valence >= -1.0 and v.valence <= 1.0
            assert v.arousal >= 0.0 and v.arousal <= 1.0

        # 4. Test Physiological Synchronization & Tension Resonance Trajectory
        print("\n[TEST 4] Testing Physiological Resonance Dossier & Tension Trajectory...")
        report = spatial_biometrics_service.generate_resonance_report(movie_id=movie.id, db=db)
        assert len(report.resonance_curve) == 10
        assert 0 <= report.physiological_synchronization_score <= 100
        assert 0 <= report.autonomic_coherence_score <= 100
        print(f"✅ Generated Physiological Resonance Report for \"{report.movie_title}\":")
        print(f"   • Physiological Sync Score: {report.physiological_synchronization_score:.1f}%")
        print(f"   • Autonomic Coherence:      {report.autonomic_coherence_score:.1f}%")
        print(f"   • Dominant Emotional State: {report.dominant_emotional_state}")
        print(f"   • Average Heart Rate:       {report.average_heart_rate_bpm:.1f} BPM (Peak: {report.peak_heart_rate_bpm:.1f} BPM)")
        print(f"   • Recommended Ambient Glow: {report.recommended_ambient_lighting_hex}")
        print("   • 10-Point Resonance Timeline:")
        for pt in report.resonance_curve[:5]:
            alert_str = f" -> {pt.bio_alert}" if pt.bio_alert else ""
            print(f"     - [{pt.timecode_sec:4.1f}s] Film Tension: {pt.film_tension:.2f} | Viewer Arousal: {pt.viewer_arousal:.2f} | Sync: {pt.synchronization_pct:.1f}%{alert_str}")

        # 5. Test CineMesh Decentralized Edge P2P Swarm
        print("\n[TEST 5] Testing CineMesh Decentralized Edge-AI Peer Mesh Status...")
        mesh = spatial_biometrics_service.get_mesh_status()
        assert mesh.active_peers_count >= 14
        assert mesh.privacy_mode == "zero_knowledge_local_differential_privacy"
        print(f"✅ CineMesh Mainnet Connected ({mesh.mesh_id}):")
        print(f"   • Active Edge Peers:         {mesh.active_peers_count}")
        print(f"   • Local On-Device Cache:     {mesh.local_edge_cache_size_mb} MB")
        print(f"   • Privacy Architecture:      {mesh.privacy_mode}")
        for peer in mesh.connected_peers:
            print(f"     - {peer.node_name:26} | {peer.region:20} | Latency: {peer.latency_ms:2}ms | Trust: {peer.local_trust_score * 100:.0f}%")

        # 6. Test FastAPI REST Endpoints via TestClient
        print("\n[TEST 6] Testing Phase 10 FastAPI Spatial & Biometrics REST Endpoints...")
        client = TestClient(app)

        # Health & Version Check
        h_res = client.get("/")
        assert h_res.status_code == 200
        assert h_res.json()["version"] == "10.0.0"
        print("✅ GET / -> 200 OK (Version 10.0.0 verified)")

        # Environments
        e_res = client.get("/api/spatial/environments")
        assert e_res.status_code == 200
        assert len(e_res.json()) == 4
        print(f"✅ GET /api/spatial/environments -> 200 OK ({len(e_res.json())} environments)")

        # Specific Environment Details
        ed_res = client.get("/api/spatial/environments/imax_curved")
        assert ed_res.status_code == 200
        assert ed_res.json()["env_id"] == "imax_curved"
        print("✅ GET /api/spatial/environments/imax_curved -> 200 OK")

        # Audio Presets
        a_res = client.get("/api/spatial/audio-presets")
        assert a_res.status_code == 200
        assert len(a_res.json()) >= 3
        print(f"✅ GET /api/spatial/audio-presets -> 200 OK ({len(a_res.json())} presets)")

        # CineMesh Status
        m_res = client.get("/api/spatial/mesh/status")
        assert m_res.status_code == 200
        assert m_res.json()["active_peers_count"] >= 14
        print("✅ GET /api/spatial/mesh/status -> 200 OK")

        # Biometric Sync POST
        sync_payload = {
            "movie_id": movie.id,
            "current_timecode_sec": 30.0,
            "simulate_stimulus": "action_rush"
        }
        b_res = client.post("/api/spatial/biometrics/sync", json=sync_payload)
        assert b_res.status_code == 200
        assert "vitals" in b_res.json()
        print("✅ POST /api/spatial/biometrics/sync -> 200 OK (Stimulus synced)")

        # Resonance Report GET
        r_res = client.get(f"/api/spatial/biometrics/resonance/{movie.id}")
        assert r_res.status_code == 200
        assert len(r_res.json()["resonance_curve"]) == 10
        print(f"✅ GET /api/spatial/biometrics/resonance/{movie.id} -> 200 OK")

        print("\n" + "=" * 80)
        print("🎉 ALL PHASE 10 CINESPATIAL AR 3D THEATER & CINEPULSE BIOMETRICS TESTS PASSED!")
        print("=" * 80)

    finally:
        db.close()

if __name__ == "__main__":
    run_phase10_tests()
