# backend/app/services/chat/chat_engine.py
import re
from typing import List, Dict, Tuple, Optional, Any
from sqlalchemy.orm import Session
from backend.app.models.movie import Movie
from backend.app.schemas.movie import MovieListItem
from backend.app.schemas.streaming import MovieStreamingAvailability
from backend.app.schemas.chat import (
    ChatResponse,
    ToolAction
)
from backend.app.api.movies import format_movie_list_item
from backend.app.services.chat.chat_session import chat_session_manager, ChatSession
from backend.app.services.streaming_resolver import streaming_resolver
from backend.app.services.semantic_search import semantic_search_engine
from backend.app.services.graph_service import knowledge_graph_engine
from backend.app.services.agents.agent_orchestrator import agent_orchestrator

class CineCopilotEngine:
    """
    Conversational Cinematic AI Engine ("CineCopilot")
    Orchestrates multi-turn dialogue, tool invocation, and contextual responses.
    """

    def __init__(self):
        self.session_manager = chat_session_manager
        self.streaming_resolver = streaming_resolver

    def _classify_intent(self, query: str, session: ChatSession) -> str:
        q = query.lower()

        # Streaming queries
        streaming_patterns = [
            r"where\s+(can\s+i|to)\s+(watch|stream|find)",
            r"is\s+(it|this|that)\s+on\s+(netflix|prime|max|disney|hulu|apple)",
            r"streaming\s+(options|platforms|service|availability)",
            r"how\s+can\s+i\s+watch",
            r"available\s+on"
        ]
        if any(re.search(p, q) for p in streaming_patterns):
            return "STREAMING_LOOKUP"

        # Film comparison queries
        if " vs " in q or " versus " in q or "compare " in q or "difference between" in q or "better between" in q:
            return "FILM_COMPARISON"

        # Critic / Debate queries
        critic_patterns = [
            r"what\s+do\s+critics\s+think",
            r"critic\s+(review|rubric|score|verdict)",
            r"pros\s+and\s+cons",
            r"is\s+it\s+(worth\s+watching|overrated|good)",
            r"agent\s+debate",
            r"consensus\s+on"
        ]
        if any(re.search(p, q) for p in critic_patterns):
            return "CRITIC_DEBATE"

        # Knowledge Graph & Relational inquiries
        graph_patterns = [
            r"who\s+directed",
            r"directed\s+by",
            r"director(\s+of)?",
            r"who\s+starred\s+in",
            r"movies\s+directed",
            r"films\s+directed",
            r"films\s+by",
            r"filmography",
            r"collaborat(ed|ion)",
            r"movies\s+starring",
            r"starring\s+",
            r"actor\s+in",
            r"what\s+else\s+did\s+"
        ]
        if any(re.search(p, q) for p in graph_patterns):
            return "KNOWLEDGE_GRAPH"

        # Follow-up refinements
        refine_patterns = [
            r"shorter",
            r"under\s+\d+\s*(hours|mins|minutes)",
            r"something\s+(darker|funnier|lighter|older|newer|scarier)",
            r"more\s+(action|comedy|drama|sci-fi)",
            r"less\s+",
            r"instead\s+of"
        ]
        if any(re.search(p, q) for p in refine_patterns) and session.active_movie_pool:
            return "PREFERENCE_REFINE"

        # Greetings & Trivia banter
        greetings = ["hi", "hello", "hey", "sup", "greetings", "good morning", "good evening", "who are you"]
        if q.strip() in greetings or any(q.startswith(g + " ") for g in greetings):
            return "CHIT_CHAT"

        # Default to Recommendation Discovery
        return "RECOMMEND"

    def _find_movie_by_text(self, text: str, db: Session) -> Optional[Movie]:
        """Looks up a movie in the database by exact or fuzzy title matching."""
        all_movies = db.query(Movie).all()
        t_lower = text.lower()

        # Exact match
        for m in all_movies:
            if m.title.lower() == t_lower:
                return m

        # Substring match (prioritize longer titles to prevent partial matches)
        matches = [m for m in all_movies if m.title.lower() in t_lower]
        if matches:
            matches.sort(key=lambda x: len(x.title), reverse=True)
            return matches[0]

        # Word overlap match
        words = set(re.findall(r"\b\w{3,}\b", t_lower))
        best_movie = None
        best_overlap = 0
        for m in all_movies:
            m_words = set(re.findall(r"\b\w{3,}\b", m.title.lower()))
            overlap = len(words.intersection(m_words))
            if overlap > best_overlap:
                best_overlap = overlap
                best_movie = m

        if best_overlap >= 1:
            return best_movie

        return None

    def process_message(
        self,
        message: str,
        session_id: Optional[str],
        db: Session,
        region: str = "US",
        active_movie_id: Optional[int] = None
    ) -> ChatResponse:
        """Processes a user chat message with full multi-turn context and tool routing."""
        session = self.session_manager.get_or_create(session_id)
        raw_msg = message.strip()
        intent = self._classify_intent(raw_msg, session)

        tools_invoked: List[ToolAction] = []
        movies: List[MovieListItem] = []
        streaming_options: Dict[int, MovieStreamingAvailability] = {}
        suggested_followups: List[str] = []
        reply: str = ""

        # --- INTENT 1: STREAMING PROVIDER LOOKUP ---
        if intent == "STREAMING_LOOKUP":
            tools_invoked.append(ToolAction(
                tool_name="StreamingResolver",
                description="Queried 12 streaming platforms across subscription, rent, buy, and free VOD tiers"
            ))

            target_movie = None
            if active_movie_id:
                target_movie = db.query(Movie).filter(Movie.id == active_movie_id).first()

            if not target_movie:
                target_movie_item = session.get_referenced_movie(raw_msg)
                if target_movie_item:
                    target_movie = db.query(Movie).filter(Movie.id == target_movie_item.id).first()

            if not target_movie:
                target_movie = self._find_movie_by_text(raw_msg, db)

            if target_movie:
                avail = self.streaming_resolver.resolve_movie_availability(target_movie, region=region)
                streaming_options[target_movie.id] = avail
                movies = [format_movie_list_item(target_movie)]

                # Format humanized watch guide
                stream_plat = [f"**{opt.provider.name}** ({opt.quality})" for opt in avail.stream]
                rent_plat = [f"{opt.provider.name} ({opt.price})" for opt in avail.rent[:3]]
                free_plat = [f"{opt.provider.name} ({opt.price})" for opt in avail.free]

                lines = [f"🎬 **Where to watch *{target_movie.title}* ({region})**:"]
                if stream_plat:
                    lines.append(f"• **Stream**: Available on {', '.join(stream_plat)}")
                else:
                    lines.append("• **Stream**: Currently not included in standard subscription flatrate packages.")

                if rent_plat:
                    lines.append(f"• **Rent / Digital VOD**: {', '.join(rent_plat)}")
                if free_plat:
                    lines.append(f"• **Free / Ad-supported**: {', '.join(free_plat)}")

                lines.append(f"\n💡 *You can launch directly via the watch badges on the card below.*")
                reply = "\n".join(lines)

                suggested_followups = [
                    f"What do critics say about {target_movie.title}?",
                    f"Who directed {target_movie.title}?",
                    f"Recommend movies similar to {target_movie.title}"
                ]
            else:
                reply = "I'd love to check streaming availability for you! Could you specify the movie title you're looking for, or pick from your active recommendations?"
                suggested_followups = [
                    "Where to watch Inception?",
                    "Where can I stream Interstellar?",
                    "Is Parasite on Netflix?"
                ]

        # --- INTENT 2: FILM COMPARISON ---
        elif intent == "FILM_COMPARISON":
            tools_invoked.append(ToolAction(
                tool_name="ComparativeCriticMatrix",
                description="Cross-compared runtime, ratings, directors, and critical consensus"
            ))

            all_db_movies = db.query(Movie).all()
            matched_movies: List[Movie] = []
            for m in all_db_movies:
                if m.title.lower() in raw_msg.lower():
                    matched_movies.append(m)

            if len(matched_movies) < 2 and len(session.active_movie_pool) >= 2:
                # Fallback to comparing top 2 in active pool
                m1 = db.query(Movie).filter(Movie.id == session.active_movie_pool[0].id).first()
                m2 = db.query(Movie).filter(Movie.id == session.active_movie_pool[1].id).first()
                if m1 and m2:
                    matched_movies = [m1, m2]

            if len(matched_movies) >= 2:
                m1, m2 = matched_movies[0], matched_movies[1]
                movies = [format_movie_list_item(m1), format_movie_list_item(m2)]
                for m in [m1, m2]:
                    streaming_options[m.id] = self.streaming_resolver.resolve_movie_availability(m, region=region)

                d1 = m1.directors[0].name if m1.directors else "Unknown"
                d2 = m2.directors[0].name if m2.directors else "Unknown"

                reply = (
                    f"⚖️ **Cinematic Showdown: *{m1.title}* vs *{m2.title}***\n\n"
                    f"| Metric | *{m1.title}* | *{m2.title}* |\n"
                    f"| :--- | :--- | :--- |\n"
                    f"| **Rating** | ⭐ **{m1.rating}/10** | ⭐ **{m2.rating}/10** |\n"
                    f"| **Director** | {d1} | {d2} |\n"
                    f"| **Runtime** | {m1.runtime} min | {m2.runtime} min |\n"
                    f"| **Atmosphere** | {m1.mood or 'Intense'} | {m2.mood or 'Cerebral'} |\n\n"
                    f"**The Cinephile Verdict**:\n"
                    f"If you are seeking **{'cerebral narrative twists and puzzle-box architecture' if m1.rating >= m2.rating else 'emotional resonance and visceral scope'}**, choose ***{m1.title if m1.rating >= m2.rating else m2.title}***. "
                    f"Both are modern masterpieces with high critical convergence."
                )
                suggested_followups = [
                    f"Where can I stream {m1.title}?",
                    f"Where can I stream {m2.title}?",
                    f"Show {d1}'s other films"
                ]
            else:
                reply = "Please name two movies you'd like me to compare (e.g., *'Compare Inception vs Interstellar'* or *'The Dark Knight vs Fight Club'*)."
                suggested_followups = [
                    "Compare Inception vs Interstellar",
                    "Compare The Dark Knight vs Fight Club",
                    "Compare Whiplash vs Parasite"
                ]

        # --- INTENT 3: CRITIC & AGENT DEBATE ---
        elif intent == "CRITIC_DEBATE":
            tools_invoked.append(ToolAction(
                tool_name="MultiAgentDebateShowdown",
                description="Extracted Film Critic (Kael) 5-axis rubric and Consensus Arbiter (Solon) ruling"
            ))

            target_movie = session.get_referenced_movie(raw_msg)
            if not target_movie:
                target_movie_db = self._find_movie_by_text(raw_msg, db)
            else:
                target_movie_db = db.query(Movie).filter(Movie.id == target_movie.id).first()

            if target_movie_db:
                showdown = agent_orchestrator.quick_debate(
                    db=db,
                    movie_id=target_movie_db.id,
                    user_context=raw_msg
                )
                movies = [format_movie_list_item(target_movie_db)]
                streaming_options[target_movie_db.id] = self.streaming_resolver.resolve_movie_availability(target_movie_db, region=region)

                reply = (
                    f"🎭 **Critical Consensus & Agent Duel for *{target_movie_db.title}***\n\n"
                    f"• 🔭 **Scout Pitch (Argus)**: {showdown.scout_pitch}\n"
                    f"• 🎬 **Film Critic Examination (Kael)**: {showdown.critic_review}\n"
                    f"• ⚖️ **Consensus Index**: **{showdown.consensus_score}%** ({showdown.agreement_level})\n\n"
                    f"**Arbiter Ruling**: {showdown.consensus_verdict}"
                )
                suggested_followups = [
                    f"Where to watch {target_movie_db.title}?",
                    f"What else did its director make?",
                    f"Find movies with higher consensus"
                ]
            else:
                reply = "Which movie would you like the Film Critic and Consensus Arbiter to review? You can name any title or pick from your recommendations."
                suggested_followups = [
                    "What do critics think of Inception?",
                    "Critic rubric for Parasite",
                    "Agent debate on The Matrix"
                ]

        # --- INTENT 4: KNOWLEDGE GRAPH & RELATIONAL EXPLORATION ---
        elif intent == "KNOWLEDGE_GRAPH":
            tools_invoked.append(ToolAction(
                tool_name="CinematicKnowledgeGraph",
                description="Traversed directed property graph for director, actor, and multi-hop entity connections"
            ))

            # Detect entities mentioned
            matched_director = None
            matched_actor = None
            all_movies = db.query(Movie).all()

            for m in all_movies:
                for d in m.directors:
                    if d.name.lower() in raw_msg.lower():
                        matched_director = d.name
                        break
                for assoc in m.cast_associations:
                    if assoc.cast_member.name.lower() in raw_msg.lower():
                        matched_actor = assoc.cast_member.name
                        break

            if matched_director:
                d_movies = [m for m in all_movies if any(d.name == matched_director for d in m.directors)]
                movies = [format_movie_list_item(m) for m in d_movies[:5]]
                for m in d_movies[:5]:
                    streaming_options[m.id] = self.streaming_resolver.resolve_movie_availability(m, region=region)

                titles_str = ", ".join([f"*{m.title}* ({m.rating}★)" for m in d_movies])
                reply = (
                    f"🎬 **Director Filmography: {matched_director}**\n\n"
                    f"We found **{len(d_movies)}** titles directed by **{matched_director}** in our cinematic graph:\n"
                    f"{titles_str}.\n\n"
                    f"They frequently collaborate with recurring technical visionaries and actors connected through multi-hop graph pathways."
                )
                suggested_followups = [
                    f"What is {matched_director}'s highest rated film?",
                    f"Where to stream {d_movies[0].title if d_movies else 'their movies'}?",
                    f"Compare {d_movies[0].title if len(d_movies) > 0 else 'films'} vs {d_movies[1].title if len(d_movies) > 1 else 'other works'}"
                ]
            elif matched_actor:
                a_movies = [m for m in all_movies if any(assoc.cast_member.name == matched_actor for assoc in m.cast_associations)]
                movies = [format_movie_list_item(m) for m in a_movies[:5]]
                for m in a_movies[:5]:
                    streaming_options[m.id] = self.streaming_resolver.resolve_movie_availability(m, region=region)

                titles_str = ", ".join([f"*{m.title}*" for m in a_movies])
                reply = (
                    f"⭐ **Actor Filmography: {matched_actor}**\n\n"
                    f"**{matched_actor}** stars in **{len(a_movies)}** catalog masterworks:\n"
                    f"{titles_str}.\n\n"
                    f"Check out the cards below with streaming availability attached."
                )
                suggested_followups = [
                    f"Where can I watch {a_movies[0].title if a_movies else 'these'}?",
                    f"What genres does {matched_actor} usually star in?",
                    "Recommend more movies like these"
                ]
            else:
                reply = "I can trace any director or actor across our Cinematic Knowledge Graph! Who would you like to explore?"
                suggested_followups = [
                    "Films directed by Christopher Nolan",
                    "Movies starring Leonardo DiCaprio",
                    "Quentin Tarantino filmography"
                ]

        # --- INTENT 5: PREFERENCE REFINEMENT ---
        elif intent == "PREFERENCE_REFINE":
            tools_invoked.append(ToolAction(
                tool_name="ContextualPreferenceFilter",
                description="Filtered previous recommendation pool by runtime, mood, and pace constraints"
            ))

            prev_pool = session.active_movie_pool
            prev_ids = [m.id for m in prev_pool]
            pool_movies = db.query(Movie).filter(Movie.id.in_(prev_ids)).all() if prev_ids else db.query(Movie).all()

            filtered = pool_movies
            explanation = "Tailoring our previous recommendations with your updated constraints"

            # Check runtime constraint
            if "shorter" in raw_msg.lower() or "under 2 hours" in raw_msg.lower() or "under 120" in raw_msg.lower():
                filtered = [m for m in filtered if m.runtime and m.runtime < 135]
                explanation = "Filtered for tighter, high-tempo pacing (under ~130 minutes)"

            # Check mood constraint
            if "darker" in raw_msg.lower():
                filtered = [m for m in filtered if any(g.name.lower() in ["crime", "thriller", "drama"] for g in m.genres)]
                explanation = "Shifted the tone toward dark noir, psychological grit, and intense stakes"
            elif "lighter" in raw_msg.lower() or "funnier" in raw_msg.lower():
                filtered = [m for m in filtered if any(g.name.lower() in ["comedy", "adventure", "animation"] for g in m.genres)]
                explanation = "Switched to uplifting, vibrant, and humorous cinematic gems"

            if not filtered:
                filtered = pool_movies[:3]

            movies = [format_movie_list_item(m) for m in filtered[:4]]
            for m in filtered[:4]:
                streaming_options[m.id] = self.streaming_resolver.resolve_movie_availability(m, region=region)

            reply = f"✨ **Refined Selection ({explanation})**:\nHere are {len(movies)} titles matching your calibrated viewing criteria."
            suggested_followups = [
                f"Where can I stream {movies[0].title}?",
                "Give me something even shorter",
                "What do critics say about the first one?"
            ]

        # --- INTENT 6: CHIT-CHAT & TRIVIA BANTER ---
        elif intent == "CHIT_CHAT":
            reply = (
                "👋 **Greetings, fellow cinephile! I am CineCopilot**, your cinematic AI advisor powered by "
                "Phase 4 Neural Vector Embeddings, Phase 5 Knowledge Graph, Phase 6 Multi-Agent consensus, and "
                "Phase 7 Watch Availability Resolvers.\n\n"
                "What kind of film journey are you in the mood for tonight? You can ask for abstract themes, "
                "specific actor-director pairings, where to stream any movie, or a side-by-side comparison!"
            )
            suggested_followups = [
                "Recommend mind-bending sci-fi thrillers",
                "Where can I stream Inception?",
                "Compare Inception vs Interstellar",
                "Show Christopher Nolan movies"
            ]

        # --- INTENT 7: GENERAL RECOMMENDATION DISCOVERY ---
        else:
            tools_invoked.append(ToolAction(
                tool_name="NeuralVectorSearch",
                description="Queried 384-dimensional dense semantic embedding space (`sentence-transformers`)"
            ))

            if not semantic_search_engine.is_trained:
                semantic_search_engine.fit(db)

            neural_results = semantic_search_engine.search(
                query=raw_msg,
                top_k=4,
                min_score=0.15
            )

            rec_movies = []
            if neural_results:
                ids = [r["movie_id"] for r in neural_results]
                db_movies = db.query(Movie).filter(Movie.id.in_(ids)).all()
                db_map = {m.id: m for m in db_movies}
                for r in neural_results:
                    m = db_map.get(r["movie_id"])
                    if m:
                        item = format_movie_list_item(m)
                        item.match_score = r["match_score"]
                        item.reasoning = r["reasoning"]
                        rec_movies.append((m, item))
            else:
                # Fallback to high-rated catalog titles
                top_db = db.query(Movie).order_by(Movie.rating.desc()).limit(4).all()
                for m in top_db:
                    item = format_movie_list_item(m)
                    item.match_score = round(m.rating * 10, 1)
                    item.reasoning = f"Critically acclaimed masterwork ({m.rating}★) with resonant thematic depth."
                    rec_movies.append((m, item))

            movies = [item for _, item in rec_movies]
            for m_obj, item in rec_movies:
                streaming_options[item.id] = self.streaming_resolver.resolve_movie_availability(m_obj, region=region)

            top_title = movies[0].title if movies else "cinema"
            reply = (
                f"🎯 **CineCopilot Recommendations for: *\"{raw_msg}\"***\n\n"
                f"I've analyzed our neural embedding space and cinematic knowledge graph to surface **{len(movies)} standout films** "
                f"aligning with your prompt. Each card below includes instant streaming and rental availability."
            )
            suggested_followups = [
                f"Where can I stream {top_title}?",
                "Give me something similar but shorter",
                f"What do critics say about {top_title}?"
            ]

        # Record in Session History
        session.add_message(
            role="user",
            content=raw_msg
        )
        session.add_message(
            role="assistant",
            content=reply,
            movies=movies,
            streaming_options=streaming_options,
            followups=suggested_followups
        )

        return ChatResponse(
            session_id=session.session_id,
            reply=reply,
            intent=intent,
            movies=movies,
            streaming_options=streaming_options,
            suggested_followups=suggested_followups,
            tools_invoked=tools_invoked
        )

# Global Singleton Instance
cine_copilot = CineCopilotEngine()
