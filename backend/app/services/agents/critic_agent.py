# backend/app/services/agents/critic_agent.py
from typing import Dict, Any, List, Optional, Tuple
from backend.app.services.agents.base_agent import BaseAgent
from backend.app.schemas.agents import PersonaProfile, CriticRubric, AgentMessage
from backend.app.models.movie import Movie

class FilmCriticAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="critic_agent_kael",
            name="Kael",
            role="Film Critic & Fact-Checker",
            avatar="🎬",
            accent_color="#f59e0b",
            description="Performs rigorous multi-metric cinematic critique, fact-checks thematic integrity, stress-tests pacing, and exposes structural flaws or clichés."
        )

    def critique_candidate(
        self,
        movie: Movie,
        persona: PersonaProfile,
        debate_rigor: str = "Balanced & Analytical"
    ) -> CriticRubric:
        """Evaluates a movie candidate on the 5-axis cinematic rubric with pros and caveats."""
        rating = movie.rating if movie.rating else 7.0
        runtime = movie.runtime if movie.runtime else 120
        genres = [g.name for g in movie.genres]
        directors = [d.name for d in movie.directors]
        overview = movie.overview or ""

        # 1. Narrative Depth & Screenplay (0-100)
        base_narrative = (rating * 9.5) - 3.0
        if any(g in ["Drama", "Mystery", "Crime"] for g in genres):
            base_narrative += 4.0
        if len(overview) > 200:
            base_narrative += 2.0
        narrative_depth = round(min(98.0, max(50.0, base_narrative)), 1)

        # 2. Visual Craft & Cinematography (0-100)
        base_visual = (rating * 9.2) + 2.0
        if any(g in ["Science Fiction", "Action", "Adventure", "Fantasy"] for g in genres):
            base_visual += 6.0
        if any(d in ["Christopher Nolan", "Denis Villeneuve", "Stanley Kubrick", "Ridley Scott", "David Fincher"] for d in directors):
            base_visual += 8.0
        visual_craft = round(min(99.0, max(55.0, base_visual)), 1)

        # 3. Pacing & Tension (0-100)
        base_pacing = 80.0 + (rating - 7.5) * 6.0
        # Runtime penalties for debate rigor
        if runtime > 155:
            if "Slow-Burn" not in persona.pacing_preference:
                base_pacing -= 6.0
        elif runtime < 95:
            base_pacing += 3.0
        pacing_tension = round(min(96.0, max(48.0, base_pacing)), 1)

        # 4. Emotional & Intellectual Resonance (0-100)
        base_resonance = (rating * 9.0)
        if any(g in ["Drama", "Animation", "Romance"] for g in genres):
            base_resonance += 5.0
        emotional_resonance = round(min(98.0, max(50.0, base_resonance)), 1)

        # 5. Thematic Fidelity to Persona Profile (0-100)
        fidelity_matches = sum(1 for g in genres if g in persona.preferred_genres)
        thematic_fidelity = round(min(99.0, max(60.0, 70.0 + (fidelity_matches * 8.0))), 1)

        # Apply Debate Rigor adjustments
        rigor_multiplier = 1.0
        if debate_rigor == "Gentle & Agreeable":
            rigor_multiplier = 1.05
        elif debate_rigor == "Fierce & Ruthless":
            rigor_multiplier = 0.90
            narrative_depth = round(narrative_depth * 0.92, 1)
            pacing_tension = round(pacing_tension * 0.88, 1)

        overall_critic_score = round(min(99.0, max(45.0, (
            narrative_depth * 0.25 +
            visual_craft * 0.25 +
            pacing_tension * 0.20 +
            emotional_resonance * 0.15 +
            thematic_fidelity * 0.15
        ) * rigor_multiplier)), 1)

        # Pros generation
        pros = []
        if visual_craft >= 88:
            pros.append(f"Masterclass visual framing and technical sound design ({visual_craft}% Visual Craft)")
        if narrative_depth >= 85:
            pros.append(f"Tightly woven screenplay with layered intellectual depth ({narrative_depth}% Narrative)")
        if directors:
            pros.append(f"Commanding directorial execution from {directors[0]}")
        if pacing_tension >= 84:
            pros.append("Superb tension escalation that sustains viewer engagement")
        if not pros:
            pros.append(f"Reliable genre execution backed by a {rating}/10 critical reception")

        # Caveats generation
        caveats = []
        if runtime > 150:
            caveats.append(f"Demanding runtime ({runtime} min) requires sustained viewer focus")
        if pacing_tension < 75:
            caveats.append("Deliberate early-act pacing may test impatient viewers")
        if debate_rigor == "Fierce & Ruthless":
            caveats.append("Features genre-standard exposition beats in the secondary act")
        if any(d_trope in overview.lower() for d_trope in ["cliché", "generic", "predictable"]):
            caveats.append("Relies on familiar genre tropes in resolution")
        if not caveats:
            caveats.append("Minor stylistic polarization depending on mood preference")

        # Critique summary
        summary_tone = "Exceptional masterwork" if overall_critic_score >= 88 else ("Strongly recommended entry" if overall_critic_score >= 78 else "Competent but conventional title")
        critique_summary = (
            f"Critic Verdict: {summary_tone} ({overall_critic_score}/100). "
            f"Excels in visual craft ({visual_craft}%) and narrative depth ({narrative_depth}%). "
            f"Caution: {caveats[0]}."
        )

        return CriticRubric(
            narrative_depth=narrative_depth,
            visual_craft=visual_craft,
            pacing_tension=pacing_tension,
            emotional_resonance=emotional_resonance,
            thematic_fidelity=thematic_fidelity,
            overall_critic_score=overall_critic_score,
            pros=pros[:3],
            caveats=caveats[:2],
            critique_summary=critique_summary
        )

    def review_candidate_pool(
        self,
        candidates: List[Dict[str, Any]],
        persona: PersonaProfile,
        debate_rigor: str = "Balanced & Analytical"
    ) -> Tuple[List[Dict[str, Any]], AgentMessage]:
        """Critiques all scouted candidates and appends CriticRubric to candidate dicts."""
        critiqued_candidates = []
        for c in candidates:
            movie = c["movie"]
            rubric = self.critique_candidate(movie, persona, debate_rigor)
            c_copy = dict(c)
            c_copy["critic_rubric"] = rubric
            c_copy["critic_score"] = rubric.overall_critic_score
            critiqued_candidates.append(c_copy)

        # Build Critic Deliberation message
        avg_score = round(sum(c["critic_score"] for c in critiqued_candidates) / max(1, len(critiqued_candidates)), 1)
        top_critic_picks = sorted(critiqued_candidates, key=lambda x: x["critic_score"], reverse=True)
        top_title = top_critic_picks[0]["movie"].title if top_critic_picks else "None"
        
        critic_msg_content = (
            f"🎬 **Film Critic Cross-Examination Completed**: Evaluated {len(critiqued_candidates)} candidates "
            f"under **{debate_rigor}** standard. Average Critic Index: {avg_score}/100. "
            f"Highest artistic acclaim awarded to \"{top_title}\" ({top_critic_picks[0]['critic_score']}%). "
            f"Flagged runtime and pacing caveats on select proposals. Ready for Arbiter synthesis."
        )

        agent_msg = self.create_message(
            round_index=3,
            message_type="critic_review",
            content=critic_msg_content,
            confidence=0.92
        )

        return critiqued_candidates, agent_msg
