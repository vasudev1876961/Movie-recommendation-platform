# backend/app/services/agents/agent_orchestrator.py
import time
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.app.services.agents.persona_agent import PersonaProfilerAgent, ARCHETYPES
from backend.app.services.agents.scout_agent import CandidateScoutAgent
from backend.app.services.agents.critic_agent import FilmCriticAgent
from backend.app.services.agents.arbiter_agent import ConsensusArbiterAgent
from backend.app.services.agents.strategist_agent import ViewingStrategistAgent
from backend.app.schemas.agents import (
    AgentDeliberationResponse,
    AgentConsensusMovie,
    QuickDebateResponse,
    AgentMessage
)
from backend.app.api.movies import format_movie_list_item
from backend.app.models.movie import Movie

class MultiAgentOrchestrator:
    def __init__(self):
        self.persona_agent = PersonaProfilerAgent()
        self.scout_agent = CandidateScoutAgent()
        self.critic_agent = FilmCriticAgent()
        self.arbiter_agent = ConsensusArbiterAgent()
        self.strategist_agent = ViewingStrategistAgent()

    def get_roster(self) -> List[Dict[str, Any]]:
        return [
            self.persona_agent.get_descriptor(),
            self.scout_agent.get_descriptor(),
            self.critic_agent.get_descriptor(),
            self.arbiter_agent.get_descriptor(),
            self.strategist_agent.get_descriptor()
        ]

    def get_personas(self) -> Dict[str, Any]:
        return ARCHETYPES

    def deliberate(
        self,
        query: str,
        db: Session,
        archetype: str = "The Adaptive Cinephile",
        debate_rigor: str = "Balanced & Analytical",
        limit: int = 5,
        user_id: Optional[int] = None
    ) -> AgentDeliberationResponse:
        """Executes the full 5-agent consensus deliberation workflow."""
        start_time = time.time()
        deliberation_log: List[AgentMessage] = []
        timings: Dict[str, float] = {}

        # Round 1: Persona Profiling
        t0 = time.time()
        persona, msg1 = self.persona_agent.analyze_profile(
            query=query,
            archetype_name=archetype
        )
        deliberation_log.append(msg1)
        timings["persona_agent_ms"] = round((time.time() - t0) * 1000, 2)

        # Round 2: Candidate Scouting
        t0 = time.time()
        pool_size = max(10, limit * 2)
        candidates, msg2 = self.scout_agent.scout_candidates(
            query=query,
            persona=persona,
            db=db,
            pool_size=pool_size,
            user_id=user_id
        )
        deliberation_log.append(msg2)
        timings["scout_agent_ms"] = round((time.time() - t0) * 1000, 2)

        if not candidates:
            # Fallback if catalog was empty
            all_m = db.query(Movie).order_by(Movie.rating.desc()).limit(limit).all()
            candidates = [{
                "movie": m,
                "movie_id": m.id,
                "scout_score": 80.0,
                "discovery_source": "Catalog Quality Prior",
                "scout_pitch": f"Curated title {m.title} with high critical reception.",
                "sources": ["Database"]
            } for m in all_m]

        # Round 3: Film Critic Cross-Examination
        t0 = time.time()
        critiqued, msg3 = self.critic_agent.review_candidate_pool(
            candidates=candidates,
            persona=persona,
            debate_rigor=debate_rigor
        )
        deliberation_log.append(msg3)
        timings["critic_agent_ms"] = round((time.time() - t0) * 1000, 2)

        # Round 4: Consensus Arbitration
        t0 = time.time()
        arbitrated, msg4 = self.arbiter_agent.arbitrate_candidates(
            critiqued_candidates=critiqued,
            limit=limit
        )
        deliberation_log.append(msg4)
        timings["arbiter_agent_ms"] = round((time.time() - t0) * 1000, 2)

        # Round 5: Viewing Strategy & Double Feature Pairing
        t0 = time.time()
        final_candidates, msg5 = self.strategist_agent.enhance_candidates(
            consensus_candidates=arbitrated,
            db=db
        )
        deliberation_log.append(msg5)
        timings["strategist_agent_ms"] = round((time.time() - t0) * 1000, 2)

        total_elapsed_ms = round((time.time() - start_time) * 1000, 2)
        timings["total_pipeline_ms"] = total_elapsed_ms

        # Assemble AgentConsensusMovie items
        recommendations: List[AgentConsensusMovie] = []
        for c in final_candidates:
            movie_item = format_movie_list_item(c["movie"])
            recommendations.append(AgentConsensusMovie(
                movie=movie_item,
                consensus_score=c["consensus_score"],
                agreement_level=c["agreement_level"],
                scout_pitch=c["scout_pitch"],
                discovery_source=c["discovery_source"],
                critic_rubric=c["critic_rubric"],
                arbiter_synthesis=c["arbiter_synthesis"],
                viewing_dossier=c["viewing_dossier"],
                scout_score=c["scout_score"],
                critic_score=c["critic_score"]
            ))

        executive_summary = (
            f"The Multi-Agent Network evaluated {len(candidates)} candidates across {len(deliberation_log)} deliberation rounds. "
            f"Delivered {len(recommendations)} consensus-ranked discoveries tailored to \"{query}\" with a **{archetype}** persona lens."
        )

        return AgentDeliberationResponse(
            query=query,
            archetype=archetype,
            debate_rigor=debate_rigor,
            persona=persona,
            deliberation_log=deliberation_log,
            recommendations=recommendations,
            executive_summary=executive_summary,
            total_rounds=len(deliberation_log),
            telemetry={
                "agent_count": 5,
                "timings_ms": timings,
                "candidates_scouted": len(candidates),
                "candidates_ranked": len(recommendations)
            }
        )

    def quick_debate(
        self,
        db: Session,
        movie_id: Optional[int] = None,
        movie_title: Optional[str] = None,
        user_context: Optional[str] = None,
        debate_rigor: str = "Balanced & Analytical"
    ) -> Optional[QuickDebateResponse]:
        """Conducts a rapid 2-round Scout vs Critic debate showdown on a specific movie."""
        movie = None
        if movie_id:
            movie = db.query(Movie).filter(Movie.id == movie_id).first()
        elif movie_title:
            movie = db.query(Movie).filter(Movie.title.ilike(f"%{movie_title}%")).first()

        if not movie:
            return None

        # Build basic persona
        persona, _ = self.persona_agent.analyze_profile(
            query=user_context or movie.title,
            archetype_name="The Auteur Cinephile"
        )

        # 1. Scout Pitch
        genres_str = ", ".join([g.name for g in movie.genres])
        directors_str = ", ".join([d.name for d in movie.directors]) or "Acclaimed Director"
        scout_score = min(98.0, max(65.0, (movie.rating * 9.5) + 5.0))
        scout_pitch = (
            f"\"{movie.title}\" is an essential {genres_str} masterstroke directed by {directors_str}. "
            f"With a {movie.rating}/10 critical rating, it delivers transcendent worldbuilding and visceral thematic power."
        )

        scout_msg = self.scout_agent.create_message(
            round_index=1,
            message_type="scout_pitch",
            content=f"🔭 **Scout Opening Argument**: {scout_pitch}",
            confidence=0.95
        )

        # 2. Critic Review
        critic_rubric = self.critic_agent.critique_candidate(
            movie=movie,
            persona=persona,
            debate_rigor=debate_rigor
        )

        critic_review = (
            f"While {movie.title} demonstrates formidable visual craft ({critic_rubric.visual_craft}%), "
            f"we must scrutinize its pacing ({critic_rubric.pacing_tension}%). "
            f"{critic_rubric.caveats[0]}."
        )

        critic_msg = self.critic_agent.create_message(
            round_index=2,
            message_type="critic_review",
            content=f"🎬 **Critic Rebuttal**: {critic_review}",
            confidence=0.93
        )

        # 3. Consensus Synthesis
        consensus_score = round((scout_score * 0.48) + (critic_rubric.overall_critic_score * 0.52), 1)
        delta = abs(scout_score - critic_rubric.overall_critic_score)
        agreement_level = "Unanimous Consensus" if delta <= 5 else ("Strong Agreement" if delta <= 12 else "Nuanced Compromise")
        
        verdict = (
            f"Arbiter Ruling ({consensus_score}% - {agreement_level}): "
            f"\"{movie.title}\" is certified as a top-tier recommendation. "
            f"The Scout's thematic discovery and Critic's artistic appraisal ({critic_rubric.overall_critic_score}/100) confirm high viewing priority."
        )

        arbiter_msg = self.arbiter_agent.create_message(
            round_index=3,
            message_type="consensus_verdict",
            content=f"⚖️ **Consensus Verdict**: {verdict}",
            confidence=0.98
        )

        transcript = [scout_msg, critic_msg, arbiter_msg]

        return QuickDebateResponse(
            movie=format_movie_list_item(movie),
            scout_pitch=scout_pitch,
            critic_review=critic_review,
            critic_rubric=critic_rubric,
            consensus_score=consensus_score,
            consensus_verdict=verdict,
            agreement_level=agreement_level,
            debate_transcript=transcript
        )

# Global singleton orchestrator
agent_orchestrator = MultiAgentOrchestrator()
