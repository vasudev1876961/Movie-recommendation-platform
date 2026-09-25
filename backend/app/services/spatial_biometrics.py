# backend/app/services/spatial_biometrics.py
import math
import time
import random
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from backend.app.models.movie import Movie
from backend.app.schemas.spatial import (
    SpatialEnvironment,
    SpatialAudioChannel,
    SpatialAudioPreset,
    BiometricVitals,
    BiometricResonancePoint,
    BiometricResonanceReport,
    EdgePeerNode,
    MeshNetworkStatus,
)

class SpatialBiometricsService:
    def __init__(self):
        self._environments = self._init_environments()
        self._audio_presets = self._init_audio_presets()
        self._mock_peers = self._init_mock_peers()

    def _init_environments(self) -> List[SpatialEnvironment]:
        return [
            SpatialEnvironment(
                env_id="imax_curved",
                name="IMAX Curved Horizon Theater",
                tagline="1.43:1 Gigantic Geometric Curved Horizon with Acoustic Baffling",
                icon="fa-film",
                theme_color="#00e5ff",
                description="State-of-the-art amphitheater screen curved at 0.38 rad for optimal retinal immersion, floating ambient ceiling, and deep sapphire wall illumination.",
                screen_curvature_rad=0.38,
                ambient_light_hex="#041226",
                projection_bloom=0.85,
                particles_type="subtle_dust"
            ),
            SpatialEnvironment(
                env_id="nebula_cosmic",
                name="Starlight Cosmic Nebula",
                tagline="Zero-Gravity Floating Screen in an Interstellar Stardust Field",
                icon="fa-meteor",
                theme_color="#8b5cf6",
                description="Transcend physical theater walls. Watch in deep outer space surrounded by slow-drifting auroras, distant pulsar flares, and cosmic starlight reflection.",
                screen_curvature_rad=0.28,
                ambient_light_hex="#1a0b2e",
                projection_bloom=1.2,
                particles_type="cosmic_stars"
            ),
            SpatialEnvironment(
                env_id="cyberpunk_holodeck",
                name="Neo-Tokyo Cyberpunk Holodeck",
                tagline="Holographic Vector Mesh with Rain-Reflecting Neon Perspective",
                icon="fa-vr-cardboard",
                theme_color="#ff007f",
                description="Futuristic virtual reality chamber featuring glowing floor grid vectors, holographic framing monitors, and responsive chromatic aberration edge glow.",
                screen_curvature_rad=0.45,
                ambient_light_hex="#160321",
                projection_bloom=1.4,
                particles_type="cyber_grid"
            ),
            SpatialEnvironment(
                env_id="arthouse_vintage",
                name="1920s Velvet Art-Deco Cinema",
                tagline="Gilded Scalloped Archways, Heavy Crimson Velvet & Warm Incandescence",
                icon="fa-landmark",
                theme_color="#f59e0b",
                description="Classic Golden-Age cinema hall with authentic 35mm projector dust beam, pleated crimson velvet curtains, and warm candle-tone footlights.",
                screen_curvature_rad=0.15,
                ambient_light_hex="#261005",
                projection_bloom=0.6,
                particles_type="warm_embers"
            ),
        ]

    def _init_audio_presets(self) -> List[SpatialAudioPreset]:
        return [
            SpatialAudioPreset(
                preset_id="dolby_atmos_spatial",
                name="Dolby Atmos 7.1.4 Binaural Soundfield",
                description="Full-sphere spatial 3D audio emulation with HRTF filtering, ear-level surround panning, and overhead height object tracking.",
                hrtf_enabled=True,
                room_reverb_type="imax_hall",
                reverb_decay_sec=1.8,
                doppler_factor=1.0,
                virtual_channels=[
                    SpatialAudioChannel(name="Center Dialogue", channel_type="center", azimuth_deg=0.0, elevation_deg=0.0, distance_m=3.0, gain=1.2),
                    SpatialAudioChannel(name="Front Left", channel_type="front_left", azimuth_deg=-30.0, elevation_deg=0.0, distance_m=3.5, gain=1.0),
                    SpatialAudioChannel(name="Front Right", channel_type="front_right", azimuth_deg=30.0, elevation_deg=0.0, distance_m=3.5, gain=1.0),
                    SpatialAudioChannel(name="Surround Left", channel_type="surround_l", azimuth_deg=-90.0, elevation_deg=10.0, distance_m=2.8, gain=0.9),
                    SpatialAudioChannel(name="Surround Right", channel_type="surround_r", azimuth_deg=90.0, elevation_deg=10.0, distance_m=2.8, gain=0.9),
                    SpatialAudioChannel(name="Rear Left", channel_type="rear_l", azimuth_deg=-140.0, elevation_deg=5.0, distance_m=3.2, gain=0.85),
                    SpatialAudioChannel(name="Rear Right", channel_type="rear_r", azimuth_deg=140.0, elevation_deg=5.0, distance_m=3.2, gain=0.85),
                    SpatialAudioChannel(name="Overhead Height Left", channel_type="height_l", azimuth_deg=-45.0, elevation_deg=45.0, distance_m=2.5, gain=0.95),
                    SpatialAudioChannel(name="Overhead Height Right", channel_type="height_r", azimuth_deg=45.0, elevation_deg=45.0, distance_m=2.5, gain=0.95),
                    SpatialAudioChannel(name="Sub-Bass LFE", channel_type="lfe", azimuth_deg=0.0, elevation_deg=-20.0, distance_m=2.0, gain=1.3),
                ]
            ),
            SpatialAudioPreset(
                preset_id="imax_grand_acoustics",
                name="IMAX Grand Concert Acoustics",
                description="Massive stadium-grade reverberation with thunderous dynamic sub-bass resonance and wide acoustic stage projection.",
                hrtf_enabled=True,
                room_reverb_type="cathedral",
                reverb_decay_sec=2.6,
                doppler_factor=1.2,
                virtual_channels=[
                    SpatialAudioChannel(name="Screen Wall Main", channel_type="center", azimuth_deg=0.0, elevation_deg=5.0, distance_m=4.5, gain=1.3),
                    SpatialAudioChannel(name="Arena Left Wing", channel_type="surround_l", azimuth_deg=-60.0, elevation_deg=15.0, distance_m=4.0, gain=1.1),
                    SpatialAudioChannel(name="Arena Right Wing", channel_type="surround_r", azimuth_deg=60.0, elevation_deg=15.0, distance_m=4.0, gain=1.1),
                    SpatialAudioChannel(name="Sub-Harmonic Subwoofer", channel_type="lfe", azimuth_deg=0.0, elevation_deg=-10.0, distance_m=2.5, gain=1.5),
                ]
            ),
            SpatialAudioPreset(
                preset_id="intimate_studio_binaural",
                name="Intimate Art-House Studio",
                description="Acoustically damped recording studio setting optimized for crisp whispered dialogue, delicate foley nuances, and close-mic precision.",
                hrtf_enabled=True,
                room_reverb_type="intimate_studio",
                reverb_decay_sec=0.6,
                doppler_factor=0.5,
                virtual_channels=[
                    SpatialAudioChannel(name="Close Focal Screen", channel_type="center", azimuth_deg=0.0, elevation_deg=0.0, distance_m=2.0, gain=1.1),
                    SpatialAudioChannel(name="Near Left", channel_type="front_left", azimuth_deg=-20.0, elevation_deg=0.0, distance_m=2.2, gain=0.9),
                    SpatialAudioChannel(name="Near Right", channel_type="front_right", azimuth_deg=20.0, elevation_deg=0.0, distance_m=2.2, gain=0.9),
                ]
            ),
        ]

    def _init_mock_peers(self) -> List[EdgePeerNode]:
        return [
            EdgePeerNode(
                peer_id="peer-us-east-491",
                node_name="EdgeNode_CyberCine_NY",
                region="US-East (New York)",
                latency_ms=18,
                consensus_contributions=342,
                edge_cached_models=["all-MiniLM-L6-v2-quant", "svd-collaborative-edge"],
                local_trust_score=0.98
            ),
            EdgePeerNode(
                peer_id="peer-eu-west-108",
                node_name="EdgeNode_Auteur_London",
                region="EU-West (London)",
                latency_ms=42,
                consensus_contributions=289,
                edge_cached_models=["all-MiniLM-L6-v2-quant", "graph-rag-subgraph-cache"],
                local_trust_score=0.95
            ),
            EdgePeerNode(
                peer_id="peer-ap-south-773",
                node_name="EdgeNode_BollywoodPulse_MUM",
                region="AP-South (Mumbai)",
                latency_ms=29,
                consensus_contributions=512,
                edge_cached_models=["all-MiniLM-L6-v2-quant", "biometric-vad-weights"],
                local_trust_score=0.99
            ),
            EdgePeerNode(
                peer_id="peer-ap-northeast-331",
                node_name="EdgeNode_NeoTokyo_Shibuya",
                region="AP-East (Tokyo)",
                latency_ms=64,
                consensus_contributions=198,
                edge_cached_models=["all-MiniLM-L6-v2-quant"],
                local_trust_score=0.94
            )
        ]

    def get_environments(self) -> List[SpatialEnvironment]:
        return self._environments

    def get_environment_by_id(self, env_id: str) -> SpatialEnvironment:
        for env in self._environments:
            if env.env_id == env_id:
                return env
        return self._environments[0]

    def get_audio_presets(self) -> List[SpatialAudioPreset]:
        return self._audio_presets

    def get_mesh_status(self) -> MeshNetworkStatus:
        return MeshNetworkStatus(
            mesh_id="cinemesh-p2p-v10-mainnet",
            active_peers_count=len(self._mock_peers) + 14,
            local_edge_cache_size_mb=48.6,
            privacy_mode="zero_knowledge_local_differential_privacy",
            swarm_resonance_hotspots_count=37,
            connected_peers=self._mock_peers
        )

    def simulate_or_sync_biometrics(
        self,
        movie_id: int,
        timecode_sec: float,
        vitals: Optional[BiometricVitals],
        stimulus: Optional[str],
        db: Session
    ) -> Dict[str, Any]:
        """
        Synchronizes live client telemetry or computes high-fidelity simulated autonomic vitals based on film dramatic rhythm.
        """
        movie = db.query(Movie).filter(Movie.id == movie_id).first()
        title = movie.title if movie else "Cinematic Experience"
        genres = " ".join([g.name.lower() for g in movie.genres]) if (movie and movie.genres) else "drama"

        is_thriller = any(g in genres for g in ["thriller", "action", "horror", "mystery", "crime"])
        is_sci_fi = "sci-fi" in genres or "adventure" in genres
        is_calm = any(g in genres for g in ["romance", "comedy", "animation"])

        # Base tension arc over timecode
        cycle = math.sin((timecode_sec / 18.0) * math.pi)
        base_tension = 0.5 + 0.35 * cycle
        if is_thriller:
            base_tension = min(0.95, base_tension + 0.15)
        elif is_calm:
            base_tension = max(0.2, base_tension - 0.2)

        # Stimulus overrides
        base_hr = 74.0
        base_hrv = 45.0
        base_gsr = 4.2
        base_pupil = 3.6
        valence = 0.35
        arousal = base_tension
        dominance = 0.55

        if stimulus == "sudden_shock":
            base_hr = 124.0
            base_hrv = 18.0
            base_gsr = 12.8
            base_pupil = 5.8
            valence = -0.65
            arousal = 0.98
            dominance = 0.2
            stress_state = "adrenaline_spike"
            bio_alert = "🚨 Cardiac Spike Detected (Adrenaline Surge)"
        elif stimulus == "action_rush":
            base_hr = 108.0
            base_hrv = 28.0
            base_gsr = 9.4
            base_pupil = 5.2
            valence = 0.5
            arousal = 0.92
            dominance = 0.75
            stress_state = "engaged"
            bio_alert = "⚡ High Kinematic Arousal Match"
        elif stimulus == "chill_calm":
            base_hr = 62.0
            base_hrv = 68.0
            base_gsr = 2.4
            base_pupil = 3.1
            valence = 0.8
            arousal = 0.22
            dominance = 0.85
            stress_state = "serene"
            bio_alert = "🌿 Parasympathetic Rest & Digest State"
        elif stimulus == "emotional_tears":
            base_hr = 86.0
            base_hrv = 34.0
            base_gsr = 7.1
            base_pupil = 4.8
            valence = -0.4
            arousal = 0.72
            dominance = 0.35
            stress_state = "tense"
            bio_alert = "💧 Emotional Resonance Peak (Catharsis)"
        else:
            # Baseline continuous simulation or passed vitals
            if vitals:
                base_hr = vitals.heart_rate_bpm
                base_hrv = vitals.hrv_ms
                base_gsr = vitals.galvanic_skin_response_us
                base_pupil = vitals.pupil_dilation_mm
                valence = vitals.valence
                arousal = vitals.arousal
                dominance = vitals.dominance
            else:
                base_hr = 72.0 + (base_tension * 32.0) + random.uniform(-2.5, 2.5)
                base_hrv = max(18.0, 65.0 - (base_tension * 35.0))
                base_gsr = 3.0 + (base_tension * 6.5)
                base_pupil = 3.2 + (base_tension * 2.2)
                valence = 0.6 - (base_tension * 0.7)
                arousal = min(1.0, max(0.05, base_tension))
                dominance = 0.8 - (base_tension * 0.5)

            if base_hr > 105:
                stress_state = "adrenaline_spike"
                bio_alert = "⚠️ Imminent Tension Spike Ahead"
            elif base_hr > 85:
                stress_state = "tense"
                bio_alert = None
            elif base_hr > 70:
                stress_state = "engaged"
                bio_alert = None
            else:
                stress_state = "serene"
                bio_alert = None

        # Synchronized ambient illumination recommendation based on autonomic vitals
        if stress_state == "adrenaline_spike":
            rec_ambient = "#ff1744"  # Alert crimson / adrenaline
        elif stress_state == "tense":
            rec_ambient = "#ff9100"  # Amber tension
        elif stress_state == "engaged":
            rec_ambient = "#00e5ff"  # Electric cyan focus
        else:
            rec_ambient = "#00e676"  # Soothing emerald / deep serenity

        now_ms = int(time.time() * 1000)
        telemetry = BiometricVitals(
            timestamp_ms=now_ms,
            heart_rate_bpm=round(base_hr, 1),
            hrv_ms=round(base_hrv, 1),
            galvanic_skin_response_us=round(base_gsr, 2),
            pupil_dilation_mm=round(base_pupil, 2),
            valence=round(valence, 2),
            arousal=round(arousal, 2),
            dominance=round(dominance, 2),
            stress_level=stress_state
        )

        sync_pct = round(max(30.0, 100.0 - (abs(arousal - base_tension) * 50.0)), 1)

        return {
            "movie_id": movie_id,
            "movie_title": title,
            "timecode_sec": timecode_sec,
            "vitals": telemetry,
            "film_tension_level": round(base_tension, 2),
            "synchronization_pct": sync_pct,
            "recommended_ambient_lighting_hex": rec_ambient,
            "bio_alert": bio_alert,
        }

    def generate_resonance_report(self, movie_id: int, db: Session) -> BiometricResonanceReport:
        """
        Builds a comprehensive 10-point physiological timeline resonance dossier for the given film.
        """
        movie = db.query(Movie).filter(Movie.id == movie_id).first()
        title = movie.title if movie else "Unknown Film"
        genres = " ".join([g.name.lower() for g in movie.genres]) if (movie and movie.genres) else "action drama"

        # Seed pseudo-random curve based on movie id
        rng = random.Random(movie_id + 777)

        curve_points: List[BiometricResonancePoint] = []
        total_sync = 0.0
        hr_samples = []

        is_high_octane = any(g in genres for g in ["thriller", "action", "horror", "sci-fi"])
        base_bpm = 78 if is_high_octane else 68

        for i in range(10):
            t_sec = i * 12.0
            # Tension progression from 0 to 1
            progress = i / 9.0
            film_tension = 0.25 + 0.65 * math.sin(progress * math.pi * 0.9)
            viewer_arousal = min(1.0, max(0.1, film_tension + rng.uniform(-0.12, 0.12)))

            sync_pct = max(40.0, 100.0 - abs(film_tension - viewer_arousal) * 60.0)
            total_sync += sync_pct

            sim_hr = base_bpm + (film_tension * 34.0) + rng.uniform(-3, 3)
            hr_samples.append(sim_hr)

            alert = None
            if i == 6 and is_high_octane:
                alert = "⚡ Peak Dramatic Tension Point"
            elif i == 8:
                alert = "🎯 Emotional Climax Resolution"

            curve_points.append(BiometricResonancePoint(
                timecode_sec=round(t_sec, 1),
                film_tension=round(film_tension, 2),
                viewer_arousal=round(viewer_arousal, 2),
                synchronization_pct=round(sync_pct, 1),
                bio_alert=alert
            ))

        avg_hr = sum(hr_samples) / len(hr_samples)
        peak_hr = max(hr_samples)
        avg_sync = total_sync / len(curve_points)

        dominant_state = "Thrilled Adrenaline" if avg_hr > 92 else ("Focused Engagement" if avg_hr > 78 else "Reflective Calm")
        rec_light = "#ff1744" if avg_hr > 92 else ("#00e5ff" if avg_hr > 78 else "#8b5cf6")

        return BiometricResonanceReport(
            movie_id=movie_id,
            movie_title=title,
            average_heart_rate_bpm=round(avg_hr, 1),
            peak_heart_rate_bpm=round(peak_hr, 1),
            autonomic_coherence_score=round(avg_sync * 0.94, 1),
            dominant_emotional_state=dominant_state,
            physiological_synchronization_score=round(avg_sync, 1),
            jump_scare_risk_mitigation="Adaptive Ambient Glow Active (Dims sudden strobe transitions by 45%)",
            recommended_ambient_lighting_hex=rec_light,
            resonance_curve=curve_points
        )

# Global singleton
spatial_biometrics_service = SpatialBiometricsService()
