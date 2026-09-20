# scripts/test_phase9.py
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
from backend.app.services.neuro_studio import neuro_studio
from backend.app.main import app

def run_phase9_tests():
    print("=" * 80)
    print("MOVIEREC PHASE 9: NEURO-CINEMATIC GENERATIVE STUDIO & MULTILINGUAL VOICE SYNTHESIS")
    print("=" * 80)

    db = SessionLocal()
    try:
        # 1. Test Voice Persona Roster & Language Coverage
        print("\n[TEST 1] Testing LinguaCine Neural Voice Personas & Multi-Language Roster...")
        voices = neuro_studio.get_available_voices()
        assert len(voices) >= 12, f"Expected at least 12 voice personas, got {len(voices)}"
        
        expected_langs = {"en", "es", "fr", "ja", "de", "hi"}
        supported_langs = {v.language_code for v in voices}
        assert expected_langs.issubset(supported_langs), f"Missing languages: {expected_langs - supported_langs}"
        
        print(f"✅ Loaded {len(voices)} Voice Personas across {len(supported_langs)} global languages ({', '.join(sorted(supported_langs))}):")
        for v in voices:
            print(f"   • [{v.language_code.upper()}] {v.name:24} | {v.gender:6} | {v.archetype:32} | Pacing: {v.speech_rate}x")

        # 2. Test Curated Re-Cut Preset Vibes & Acoustic Specs
        print("\n[TEST 2] Testing CineGen Re-Cut Preset Vibes & Color Grading LUT Filters...")
        vibes = neuro_studio.get_preset_vibes()
        assert len(vibes) == 6, f"Expected 6 preset vibes, got {len(vibes)}"
        for vb in vibes:
            assert vb.lut_css_filter, f"Missing LUT filter for vibe {vb.vibe_id}"
            assert vb.soundtrack_tempo_bpm > 0, f"Invalid tempo for vibe {vb.vibe_id}"
            print(f"   • {vb.name:32} | {vb.soundtrack_tempo_bpm:3} BPM ({vb.soundtrack_key:9}) | LUT: {vb.lut_css_filter[:40]}...")

        # 3. Test Generative Trailer Re-Cutter (CineGen AI)
        print("\n[TEST 3] Testing AI Director's Cut Re-cut Treatment Generation...")
        inception = db.query(Movie).filter(Movie.title.ilike("%Inception%")).first()
        assert inception is not None, "Inception not found in catalog!"

        # Re-cut Inception as Cyberpunk Synthwave
        treatment = neuro_studio.generate_trailer_recut(
            movie_id=inception.id,
            vibe_id="cyberpunk",
            custom_prompt="Emphasize neon skyscrapers, rain reflections, and memory extraction as a corporate cybercrime.",
            db=db
        )
        assert treatment.movie_id == inception.id
        assert treatment.vibe.vibe_id == "cyberpunk"
        assert len(treatment.acts_timeline) == 4, f"Expected 4 shots/acts, got {len(treatment.acts_timeline)}"
        assert len(treatment.voiceover_monologue) > 50
        print(f"✅ Generated Cyberpunk Director's Cut for \"{treatment.movie_title}\":")
        print(f"   • Logline:        {treatment.suggested_tagline}")
        print(f"   • Remix Genre:    {treatment.remix_genre}")
        print(f"   • Live LUT CSS:   {treatment.lut_filter_css}")
        print(f"   • Soundtrack Key: {treatment.soundtrack_profile['key']} @ {treatment.soundtrack_profile['tempo_bpm']} BPM")
        print("   • 4-Act Shot Sequence:")
        for s in treatment.acts_timeline:
            print(f"     - [{s.start_sec:04.1f}s - {s.end_sec:04.1f}s] {s.act}: {s.camera_movement} -> {s.transition_type}")

        # 4. Test Multilingual Voiceover Generation across all 6 languages
        print("\n[TEST 4] Testing LinguaCine Multilingual Voiceover & Word Timing Synchronizer...")
        for lang in ["en", "es", "fr", "ja", "de", "hi"]:
            manifest = neuro_studio.generate_multilingual_dub(
                movie_id=inception.id,
                language=lang,
                db=db
            )
            assert manifest.language_code == lang
            assert len(manifest.acts) == 4, f"Expected 4 acts for {lang}"
            assert len(manifest.word_markers) > 0, f"Expected word markers for {lang}"
            assert manifest.total_estimated_duration_sec > 10.0
            
            # Verify chronological ordering of word markers
            for i in range(len(manifest.word_markers) - 1):
                curr_w = manifest.word_markers[i]
                next_w = manifest.word_markers[i+1]
                assert curr_w.start_ms < curr_w.end_ms, f"Invalid word duration: {curr_w}"
                assert curr_w.start_ms <= next_w.start_ms, f"Markers not chronological: {curr_w} vs {next_w}"

            sample_first_few = " ".join([w.word for w in manifest.word_markers[:5]])
            print(f"   • [{lang.upper()}] Voice: {manifest.voice.name:20} | Words: {len(manifest.word_markers):2} | Duration: {manifest.total_estimated_duration_sec:.1f}s | Sample: \"{sample_first_few}...\"")

        # 5. Test Export Dossier Generation
        print("\n[TEST 5] Testing Director's Cut Markdown Dossier Compilation...")
        dub_manifest = neuro_studio.generate_multilingual_dub(movie_id=inception.id, language="en", db=db)
        markdown_dossier = neuro_studio.export_treatment_markdown(treatment, dub_manifest)
        assert "# 🎬 Neuro-Cinematic Director's Cut" in markdown_dossier
        assert "Act-by-Act Shot Sequence" in markdown_dossier
        assert "LinguaCine Multilingual Voiceover" in markdown_dossier
        print(f"✅ Dossier Markdown compiled successfully ({len(markdown_dossier)} bytes).")

        # 6. Test FastAPI REST Endpoints via TestClient
        print("\n[TEST 6] Testing Phase 9 FastAPI Studio REST Endpoints via TestClient...")
        client = TestClient(app)

        # Health check
        r_health = client.get("/")
        assert r_health.status_code == 200
        assert r_health.json()["version"] == "9.0.0"
        print("✅ GET / -> 200 OK (Version 9.0.0 verified)")

        # GET /api/studio/voices
        r_voices = client.get("/api/studio/voices")
        assert r_voices.status_code == 200
        assert len(r_voices.json()) >= 12
        print(f"✅ GET /api/studio/voices -> 200 OK ({len(r_voices.json())} voices)")

        # GET /api/studio/voices?language=ja
        r_ja_voices = client.get("/api/studio/voices?language=ja")
        assert r_ja_voices.status_code == 200
        assert len(r_ja_voices.json()) >= 2
        print(f"✅ GET /api/studio/voices?language=ja -> 200 OK ({len(r_ja_voices.json())} Japanese voices)")

        # GET /api/studio/vibes
        r_vibes = client.get("/api/studio/vibes")
        assert r_vibes.status_code == 200
        assert len(r_vibes.json()) == 6
        print(f"✅ GET /api/studio/vibes -> 200 OK (6 vibes)")

        # POST /api/studio/recut
        r_recut = client.post("/api/studio/recut", json={
            "movie_id": inception.id,
            "vibe_id": "wes_anderson",
            "custom_prompt": "Center framed compositions, pastel yellow aesthetic, quirky harpsichord score."
        })
        assert r_recut.status_code == 200
        recut_data = r_recut.json()
        assert recut_data["vibe"]["vibe_id"] == "wes_anderson"
        assert len(recut_data["acts_timeline"]) == 4
        print(f"✅ POST /api/studio/recut -> 200 OK (Wes Anderson Re-cut generated for {recut_data['movie_title']})")

        # POST /api/studio/dub
        r_dub = client.post("/api/studio/dub", json={
            "movie_id": inception.id,
            "language": "es",
            "voice_id": "es_mateo"
        })
        assert r_dub.status_code == 200
        dub_data = r_dub.json()
        assert dub_data["language_code"] == "es"
        assert len(dub_data["word_markers"]) > 0
        print(f"✅ POST /api/studio/dub -> 200 OK (Spanish dub manifest generated with {len(dub_data['word_markers'])} word timing markers)")

        # POST /api/studio/export
        r_export = client.post("/api/studio/export", json={
            "treatment": recut_data,
            "dubbing": dub_data,
            "format": "markdown"
        })
        assert r_export.status_code == 200
        assert r_export.json()["format"] == "markdown"
        assert "filename" in r_export.json()
        print(f"✅ POST /api/studio/export -> 200 OK (Export filename: {r_export.json()['filename']})")

    finally:
        db.close()

    print("\n" + "=" * 80)
    print("🎉 ALL PHASE 9 NEURO-CINEMATIC STUDIO & LINGUACINE TESTS PASSED PERFECTLY!")
    print("=" * 80)

if __name__ == "__main__":
    run_phase9_tests()
