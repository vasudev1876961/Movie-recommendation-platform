# backend/app/schemas/studio.py
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

class DubbingVoice(BaseModel):
    voice_id: str
    name: str
    language_code: str
    language_name: str
    gender: str
    archetype: str
    description: str
    speech_rate: float = 1.0
    speech_pitch: float = 1.0
    sample_phrase: str

class DubbingRequest(BaseModel):
    movie_id: int
    language: str = "en"  # "en", "es", "fr", "ja", "de", "hi"
    voice_id: Optional[str] = None
    script_style: str = "epic"  # "epic", "noir", "intimate", "cerebral", "action"
    custom_monologue: Optional[str] = None

class WordTimingMarker(BaseModel):
    word: str
    start_ms: int
    end_ms: int

class ActMonologue(BaseModel):
    act_index: int
    act_name: str
    timecode: str
    speaker: str
    text: str

class DubbingManifest(BaseModel):
    movie_id: int
    movie_title: str
    language_code: str
    language_name: str
    voice: DubbingVoice
    full_script: str
    localized_title: str
    acts: List[ActMonologue]
    word_markers: List[WordTimingMarker]
    total_estimated_duration_sec: float
    acoustic_recommendation: str

class ReCutVibe(BaseModel):
    vibe_id: str
    name: str
    tagline: str
    icon: str
    primary_color: str
    lut_css_filter: str
    lut_description: str
    soundtrack_tempo_bpm: int
    soundtrack_key: str
    soundtrack_instruments: List[str]
    narrative_pacing: str

class ReCutShot(BaseModel):
    shot_number: int
    act: str
    start_sec: float
    end_sec: float
    visual_description: str
    camera_movement: str
    color_grade_treatment: str
    audio_soundscape: str
    transition_type: str
    narrator_voiceover: str

class ReCutTreatment(BaseModel):
    treatment_id: str
    movie_id: int
    movie_title: str
    original_genre: str
    vibe: ReCutVibe
    remix_genre: str
    concept_logline: str
    directorial_vision: str
    lut_filter_css: str
    soundtrack_profile: Dict[str, Any]
    acts_timeline: List[ReCutShot]
    voiceover_monologue: str
    soundscape_cues: List[str]
    suggested_tagline: str

class ReCutRequest(BaseModel):
    movie_id: int
    vibe_id: str = "cyberpunk"
    custom_prompt: Optional[str] = None
    intensity: float = 1.0

class ExportDossierRequest(BaseModel):
    treatment: ReCutTreatment
    dubbing: Optional[DubbingManifest] = None
    format: str = "markdown"  # "markdown" or "json"
