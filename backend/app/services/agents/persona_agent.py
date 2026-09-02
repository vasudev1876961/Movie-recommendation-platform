# backend/app/services/agents/persona_agent.py
import re
from typing import Dict, Any, List, Optional
from backend.app.services.agents.base_agent import BaseAgent
from backend.app.schemas.agents import PersonaProfile, AgentMessage

ARCHETYPES = {
    "The Auteur Cinephile": {
        "pacing": "Balanced to Slow-Burn",
        "complexity": "Cerebral",
        "visual_style": "Cinematographic & Auteur-Driven",
        "genres": ["Drama", "Mystery", "Thriller", "Sci-Fi"],
        "moods": ["Mind-bending", "Atmospheric", "Philosophical", "Intense"],
        "disliked": ["Formulaic exposition", "Generic CGI over-reliance", "Superficial tropes"],
        "summary": "Values directorial vision, intricate subtext, deliberate pacing, and distinctive cinematography over commercial conventions."
    },
    "The Blockbuster Thrill-Seeker": {
        "pacing": "Fast-Paced & Relentless",
        "complexity": "Accessible to Moderate",
        "visual_style": "Spectacular & High-Contrast",
        "genres": ["Action", "Adventure", "Sci-Fi"],
        "moods": ["Action-packed", "Epic", "Adrenaline", "Tense"],
        "disliked": ["Excessive dialogue without payoff", "Drab lighting", "Anti-climactic endings"],
        "summary": "Craves high-octane set-pieces, state-of-the-art audiovisual craftsmanship, and soaring adrenaline."
    },
    "The Mind-Bending Sci-Fi Architect": {
        "pacing": "Contemplative to Intense",
        "complexity": "Cerebral & High-Concept",
        "visual_style": "Futuristic & Atmospheric",
        "genres": ["Science Fiction", "Mystery", "Thriller"],
        "moods": ["Mind-bending", "Existential", "Cosmic", "Dark"],
        "disliked": ["Hand-waving scientific plot holes", "Predictable third acts", "Unmotivated romance"],
        "summary": "Obsessed with temporal paradoxes, cosmic scope, AI consciousness, and reality-altering narrative puzzles."
    },
    "The Indie Visionary Hunter": {
        "pacing": "Deliberate & Character-Focused",
        "complexity": "Nuanced & Subtextual",
        "visual_style": "Naturalistic & Poetic",
        "genres": ["Drama", "Comedy", "Romance", "Thriller"],
        "moods": ["Emotional", "Raw", "Witty", "Bittersweet"],
        "disliked": ["Sanitized corporate storytelling", "Melodramatic clichés", "Predictable arcs"],
        "summary": "Seeks human authenticity, innovative narrative structures, and bold artistic vulnerability."
    },
    "The Cozy Comfort Nostalgic": {
        "pacing": "Gentle & Engaging",
        "complexity": "Accessible & Heartfelt",
        "visual_style": "Warm & Vibrant",
        "genres": ["Animation", "Family", "Comedy", "Adventure"],
        "moods": ["Heartwarming", "Uplifting", "Playful", "Hopeful"],
        "disliked": ["Nihilistic cruelty", "Gratuitous gore", "Depressing bleakness"],
        "summary": "Appreciates heartwarming camaraderie, nostalgic warmth, witty humor, and uplifting storytelling."
    },
    "The Dark Noir & Crime Strategist": {
        "pacing": "Slow-Burn to Tense",
        "complexity": "Intricate & Morally Ambiguous",
        "visual_style": "Shadowy Neo-Noir & Gritty",
        "genres": ["Crime", "Thriller", "Mystery", "Drama"],
        "moods": ["Dark", "Suspenseful", "Grim", "Psychological"],
        "disliked": ["Naive happy endings", "Unrealistic moral binaries", "Lazy detective tropes"],
        "summary": "Enjoys gritty street realism, psychological chess matches, moral grey zones, and tense investigations."
    },
    "The Adaptive Cinephile": {
        "pacing": "Dynamic",
        "complexity": "Context-Aware",
        "visual_style": "High-Quality Cinematic",
        "genres": ["Sci-Fi", "Thriller", "Drama", "Action"],
        "moods": ["Mind-bending", "Epic", "Atmospheric"],
        "disliked": ["Generic filler", "Poorly paced third acts"],
        "summary": "Flexible cinephile tailoring expectations dynamically to match the exact thematic spirit of the prompt."
    }
}

class PersonaProfilerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="persona_agent_aura",
            name="Aura",
            role="Persona & Taste Profiler",
            avatar="🎭",
            accent_color="#a855f7",
            description="Deconstructs user prompts, archetypal affinities, psychological moods, and taste constraints into a formalized Persona Specification."
        )

    def analyze_profile(
        self,
        query: str,
        archetype_name: str = "The Adaptive Cinephile",
        user_ratings: Optional[List[Dict[str, Any]]] = None,
        watchlist: Optional[List[Dict[str, Any]]] = None
    ) -> (PersonaProfile, AgentMessage):
        """Analyzes user intent and builds structured PersonaProfile and agent message."""
        base_arch = ARCHETYPES.get(archetype_name, ARCHETYPES["The Adaptive Cinephile"])
        q_lower = query.lower()

        # Extract targeted mood cues from query
        detected_moods = list(base_arch["moods"])
        if any(w in q_lower for w in ["mind-bending", "dream", "twist", "dimension", "time", "paradox", "matrix"]):
            if "Mind-bending" not in detected_moods: detected_moods.insert(0, "Mind-bending")
        if any(w in q_lower for w in ["dark", "gritty", "noir", "killer", "violence", "horror", "gotham", "crime"]):
            if "Dark" not in detected_moods: detected_moods.insert(0, "Dark")
        if any(w in q_lower for w in ["action", "fight", "battle", "heist", "car", "fast", "adrenaline"]):
            if "Action-packed" not in detected_moods: detected_moods.insert(0, "Action-packed")
        if any(w in q_lower for w in ["emotional", "tear", "love", "heart", "family", "daughter", "father", "friend"]):
            if "Emotional" not in detected_moods: detected_moods.insert(0, "Emotional")
        if any(w in q_lower for w in ["space", "universe", "galaxy", "alien", "interstellar", "cosmos", "future"]):
            if "Cosmic Sci-Fi" not in detected_moods: detected_moods.insert(0, "Cosmic Sci-Fi")

        # Extract themes
        themes = []
        theme_map = {
            "time travel": "Temporal Mechanics & Nonlinear Time",
            "dream": "Subconscious & Dream Manipulation",
            "space": "Deep Space Isolation & Cosmic Frontier",
            "heist": "Intricate Heist & High-Stakes Strategy",
            "dystopia": "Dystopian Systems & Societal Control",
            "detective": "Noir Investigation & Deceptive Puzzles",
            "superhero": "Mythic Heroism & Moral Responsibility",
            "revenge": "Retribution & Moral Decay",
            "ai": "Artificial Intelligence & Sentience",
            "class": "Social Stratification & Satire"
        }
        for k, v in theme_map.items():
            if k in q_lower:
                themes.append(v)
        if not themes:
            themes = ["Cinematic Discovery", "Thematic Depth"]

        # Determine pacing & complexity
        pacing = base_arch["pacing"]
        if "fast" in q_lower or "adrenaline" in q_lower:
            pacing = "Fast-Paced & Relentless"
        elif "slow" in q_lower or "atmospheric" in q_lower or "deep" in q_lower:
            pacing = "Deliberate & Atmospheric Slow-Burn"

        complexity = base_arch["complexity"]
        if "complex" in q_lower or "mind-bending" in q_lower or "philosophical" in q_lower:
            complexity = "Cerebral & High-Concept"

        disliked = list(base_arch["disliked"])
        if "no horror" in q_lower or "not scary" in q_lower:
            disliked.append("Excessive horror/gore")
        if "no romance" in q_lower:
            disliked.append("Melodramatic romance")

        taste_summary = (
            f"User adopts the '{archetype_name}' lens for query \"{query}\". "
            f"Prioritizing {pacing.lower()} tempo with {complexity.lower()} complexity. "
            f"Key aesthetic: {base_arch['visual_style']}."
        )

        profile = PersonaProfile(
            archetype=archetype_name,
            target_moods=detected_moods[:4],
            preferred_genres=base_arch["genres"],
            pacing_preference=pacing,
            complexity_level=complexity,
            visual_style=base_arch["visual_style"],
            disliked_tropes=disliked,
            key_themes=themes,
            taste_summary=taste_summary
        )

        msg_content = (
            f"🎯 **Taste Profile Established**: Activated **{archetype_name}** archetype. "
            f"Targeting moods: *{', '.join(profile.target_moods)}*. "
            f"Pacing: *{profile.pacing_preference}* | Complexity: *{profile.complexity_level}*. "
            f"Themes locked: *{', '.join(profile.key_themes)}*. Disliking: *{', '.join(profile.disliked_tropes[:2])}*."
        )

        agent_msg = self.create_message(
            round_index=1,
            message_type="persona_analysis",
            content=msg_content,
            confidence=0.96
        )

        return profile, agent_msg
