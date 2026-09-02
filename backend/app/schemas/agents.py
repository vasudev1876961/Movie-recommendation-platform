# backend/app/schemas/agents.py
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from backend.app.schemas.movie import MovieListItem

class PersonaProfile(BaseModel):
    archetype: str
    target_moods: List[str]
    preferred_genres: List[str]
    pacing_preference: str  # "Fast-Paced", "Balanced", "Slow-Burn", "Contemplative"
    complexity_level: str  # "Accessible", "Moderate", "Cerebral", "Abstract"
    visual_style: str  # "Vibrant", "Dark & Gritty", "Cinematographic / Auteur", "Hyper-Realistic"
    disliked_tropes: List[str] = Field(default_factory=list)
    key_themes: List[str] = Field(default_factory=list)
    taste_summary: str

class AgentMessage(BaseModel):
    agent_id: str
    agent_name: str
    agent_role: str
    agent_avatar: str
    round_index: int
    message_type: str  # "persona_analysis", "scout_pitch", "critic_review", "rebuttal", "consensus_verdict", "strategist_plan"
    content: str
    confidence: float
    timestamp: float

class CriticRubric(BaseModel):
    narrative_depth: float  # 0-100
    visual_craft: float  # 0-100
    pacing_tension: float  # 0-100
    emotional_resonance: float  # 0-100
    thematic_fidelity: float  # 0-100
    overall_critic_score: float  # 0-100
    pros: List[str]
    caveats: List[str]
    critique_summary: str

class DoubleFeaturePairing(BaseModel):
    movie_id: int
    title: str
    poster_path: Optional[str] = None
    year: Optional[int] = None
    rating: Optional[float] = None
    pairing_rationale: str
    transition_theme: str

class ViewingDossier(BaseModel):
    optimal_setting: str  # e.g. "Late-night solo immersion with studio headphones"
    target_vibe: str  # e.g. "High-voltage adrenaline with friends"
    snack_atmosphere_pairing: str
    recommended_runtime_slot: str  # e.g. "Evening feature, distraction-free"
    double_feature: Optional[DoubleFeaturePairing] = None

class AgentConsensusMovie(BaseModel):
    movie: MovieListItem
    consensus_score: float  # 0-100
    agreement_level: str  # "Unanimous Consensus", "Strong Agreement", "Nuanced Compromise", "Polarized Debate"
    scout_pitch: str
    discovery_source: str  # e.g. "Neural Vector (384-d)", "Knowledge Graph (2-Hop)", "SVD Collaborative"
    critic_rubric: CriticRubric
    arbiter_synthesis: str
    viewing_dossier: ViewingDossier
    scout_score: float
    critic_score: float

class AgentDeliberationRequest(BaseModel):
    query: str
    archetype: Optional[str] = "The Adaptive Cinephile"
    debate_rigor: Optional[str] = "Balanced & Analytical"  # "Gentle & Agreeable", "Balanced & Analytical", "Fierce & Ruthless"
    limit: Optional[int] = 5
    user_id: Optional[int] = None

class AgentDeliberationResponse(BaseModel):
    query: str
    archetype: str
    debate_rigor: str
    persona: PersonaProfile
    deliberation_log: List[AgentMessage]
    recommendations: List[AgentConsensusMovie]
    executive_summary: str
    total_rounds: int
    telemetry: Dict[str, Any]

class QuickDebateRequest(BaseModel):
    movie_id: Optional[int] = None
    movie_title: Optional[str] = None
    user_context: Optional[str] = None
    debate_rigor: Optional[str] = "Balanced & Analytical"

class QuickDebateResponse(BaseModel):
    movie: MovieListItem
    scout_pitch: str
    critic_review: str
    critic_rubric: CriticRubric
    consensus_score: float
    consensus_verdict: str
    agreement_level: str
    debate_transcript: List[AgentMessage]
