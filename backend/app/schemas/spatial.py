# backend/app/schemas/spatial.py
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

class SpatialEnvironment(BaseModel):
    env_id: str
    name: str
    tagline: str
    icon: str
    theme_color: str
    description: str
    screen_curvature_rad: float  # e.g., 0.35 for curved IMAX
    ambient_light_hex: str
    projection_bloom: float
    particles_type: str  # "cosmic_stars", "subtle_dust", "cyber_grid", "warm_embers"

class SpatialAudioChannel(BaseModel):
    name: str
    channel_type: str  # "center", "front_left", "front_right", "surround_l", "surround_r", "height_l", "height_r", "lfe"
    azimuth_deg: float
    elevation_deg: float
    distance_m: float
    gain: float = 1.0

class SpatialAudioPreset(BaseModel):
    preset_id: str
    name: str
    description: str
    hrtf_enabled: bool = True
    room_reverb_type: str  # "cathedral", "imax_hall", "intimate_studio", "cyber_vault"
    reverb_decay_sec: float
    doppler_factor: float
    virtual_channels: List[SpatialAudioChannel]

class BiometricVitals(BaseModel):
    timestamp_ms: int
    heart_rate_bpm: float
    hrv_ms: float  # Heart rate variability (RMSSD)
    galvanic_skin_response_us: float  # Electrodermal activity in microSiemens
    pupil_dilation_mm: float
    valence: float = Field(..., ge=-1.0, le=1.0)  # Unpleasant (-1) to Pleasant (+1)
    arousal: float = Field(..., ge=0.0, le=1.0)  # Calm (0) to Excited/Intense (1)
    dominance: float = Field(..., ge=0.0, le=1.0)  # Submissive (0) to In Control (1)
    stress_level: str  # "serene", "engaged", "tense", "adrenaline_spike"

class BiometricResonancePoint(BaseModel):
    timecode_sec: float
    film_tension: float
    viewer_arousal: float
    synchronization_pct: float
    bio_alert: Optional[str] = None  # e.g., "Predicted Jump-Scare Alert"

class BiometricResonanceReport(BaseModel):
    movie_id: int
    movie_title: str
    average_heart_rate_bpm: float
    peak_heart_rate_bpm: float
    autonomic_coherence_score: float  # 0-100%
    dominant_emotional_state: str
    physiological_synchronization_score: float  # 0-100%
    jump_scare_risk_mitigation: str
    recommended_ambient_lighting_hex: str
    resonance_curve: List[BiometricResonancePoint]

class EdgePeerNode(BaseModel):
    peer_id: str
    node_name: str
    region: str
    latency_ms: int
    consensus_contributions: int
    edge_cached_models: List[str]
    local_trust_score: float

class MeshNetworkStatus(BaseModel):
    mesh_id: str
    active_peers_count: int
    local_edge_cache_size_mb: float
    privacy_mode: str  # "zero_knowledge_local_differential_privacy"
    swarm_resonance_hotspots_count: int
    connected_peers: List[EdgePeerNode]

class BiometricSyncRequest(BaseModel):
    movie_id: int
    current_timecode_sec: float = 0.0
    vitals: Optional[BiometricVitals] = None
    simulate_stimulus: Optional[str] = None  # "sudden_shock", "emotional_tears", "chill_calm", "action_rush"

class SpatialSettingsUpdateRequest(BaseModel):
    env_id: str = "imax_curved"
    audio_preset_id: str = "dolby_atmos_spatial"
    enable_head_tracking: bool = True
    enable_dynamic_ambient_sync: bool = True
    hrtf_filter_strength: float = 1.0
