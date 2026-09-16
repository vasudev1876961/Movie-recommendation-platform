# backend/app/schemas/trailer.py
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class TrailerSceneAct(BaseModel):
    act_index: int = Field(..., description="Act index: 1 (Exposition), 2 (Escalation), 3 (Climax), 4 (Stinger)")
    act_name: str = Field(..., description="Act title e.g. 'Act I: Atmospheric Setup'")
    start_time: float = Field(..., description="Start time in seconds")
    end_time: float = Field(..., description="End time in seconds")
    start_timecode: str = Field(..., description="Formatted timestamp mm:ss")
    end_timecode: str = Field(..., description="Formatted timestamp mm:ss")
    synopsis: str = Field(..., description="Cinematic micro-description of this trailer section")
    dominant_mood: str = Field(..., description="Primary emotional texture e.g. 'Ominous Anticipation'")
    shot_velocity: float = Field(..., description="Estimated cuts per minute")
    audio_intensity: float = Field(..., description="Acoustic decibel/energy index (0-100)")
    key_motifs: List[str] = Field(default_factory=list, description="Visual/narrative motifs detected in this act")

class SensoryTelemetryPoint(BaseModel):
    time: float = Field(..., description="Time in seconds")
    timecode: str = Field(..., description="Formatted timestamp mm:ss")
    tension: float = Field(..., description="Emotional tension index (0-100)")
    shot_velocity: float = Field(..., description="Cuts per minute")
    audio_energy: float = Field(..., description="Acoustic power/score crescendo (0-100)")
    visual_luminance: float = Field(..., description="Scene brightness / contrast index (0-100)")
    affective_vector: Dict[str, float] = Field(
        default_factory=dict,
        description="Normalized affective distribution (tension, adrenaline, awe, melancholia, mystery, humor)"
    )
    annotation: str = Field(..., description="Instant scene micro-synopsis")

class AestheticColorSwatch(BaseModel):
    hex: str
    name: str
    dominance_pct: float
    role: str # e.g. "Primary Key", "Atmospheric Shadow", "Accent Neon"

class AestheticDNA(BaseModel):
    aspect_ratio: str = Field(..., description="e.g. '2.39:1 Anamorphic Panavision' or '1.43:1 IMAX 70mm'")
    camera_style: str = Field(..., description="e.g. 'Fluid Steadicam & Sweeping Drone'")
    lighting_key: str = Field(..., description="e.g. 'High-Contrast Chiaroscuro & Noir Shadows'")
    color_palette: List[AestheticColorSwatch] = Field(default_factory=list)
    dominant_color_temp: str = Field(..., description="e.g. 'Cool Steel & Tungsten Gold (3800K)'")
    spoiler_risk_rating: str = Field(..., description="e.g. 'Minimal (Low Risk - Preserves 3rd Act)'")
    photosensitivity_warning: bool = Field(default=False, description="Whether rapid strobe cuts were detected")

class TrailerAnalysisResponse(BaseModel):
    movie_id: int
    movie_title: str
    trailer_key: str
    duration_seconds: int
    formatted_duration: str
    overall_pacing: str = Field(..., description="e.g. 'Hypnotic Slow-Burn with Exponential Crescendo'")
    climax_intensity: float = Field(..., description="Peak intensity score 0-100")
    acts: List[TrailerSceneAct]
    telemetry: List[SensoryTelemetryPoint]
    aesthetic_dna: AestheticDNA
    cinematic_quotes: List[str] = Field(default_factory=list)

class TrailerTwinItem(BaseModel):
    movie_id: int
    title: str
    year: Optional[str] = ""
    rating: float
    poster_path: Optional[str] = ""
    trailer_key: Optional[str] = ""
    sensory_similarity_score: float = Field(..., description="Multimodal trajectory cosine similarity (0-100%)")
    matching_pacing: str
    shared_affective_tone: str

class TrailerTwinsResponse(BaseModel):
    movie_id: int
    movie_title: str
    twins: List[TrailerTwinItem]

class TrailerVibeQuery(BaseModel):
    target_mood: Optional[str] = None
    min_tension: Optional[float] = 0.0
    min_adrenaline: Optional[float] = 0.0
    min_awe: Optional[float] = 0.0
    limit: Optional[int] = 8
