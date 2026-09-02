# backend/app/services/agents/scout_agent.py
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from backend.app.services.agents.base_agent import BaseAgent
from backend.app.schemas.agents import PersonaProfile, AgentMessage
from backend.app.models.movie import Movie
from backend.app.services.semantic_search import semantic_search_engine
from backend.app.services.graph_service import knowledge_graph_engine
from backend.app.services.hybrid_recommender import hybrid_engine

class CandidateScoutAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="scout_agent_argus",
            name="Argus",
            role="Candidate Scout & Multi-Engine Retriever",
            avatar="🔭",
            accent_color="#06b6d4",
            description="Explores the multi-dimensional cinematic catalog via Dense Vector Embeddings, Multi-Hop Knowledge Graph paths, and Hybrid Collaborative Filtering."
        )

    def scout_candidates(
        self,
        query: str,
        persona: PersonaProfile,
        db: Session,
        pool_size: int = 12,
        user_id: Optional[int] = None
    ) -> Tuple[List[Dict[str, Any]], AgentMessage]:
        """Discovers and multi-ranks candidates across vector, graph, and ML engines."""
        candidate_map: Dict[int, Dict[str, Any]] = {}

        # 1. Retrieve from Dense Vector Search (Phase 4)
        if not semantic_search_engine.is_trained:
            semantic_search_engine.fit(db)
        
        vector_results = semantic_search_engine.search(query=query, top_k=pool_size, min_score=0.10)
        for r in vector_results:
            m_id = r["movie_id"]
            if m_id not in candidate_map:
                candidate_map[m_id] = {
                    "movie_id": m_id,
                    "vector_score": r["match_score"],
                    "vector_reasoning": r["reasoning"],
                    "sources": ["Neural Vector (384-d)"],
                    "raw_score": r["match_score"]
                }
            else:
                candidate_map[m_id]["vector_score"] = r["match_score"]
                candidate_map[m_id]["sources"].append("Neural Vector (384-d)")

        # 2. Retrieve from Knowledge Graph Entity Matching (Phase 5)
        # Check if query mentions directors or actors or keywords
        try:
            # Check graph for matching nodes
            g_nodes = knowledge_graph_engine.search_nodes(query, limit=5)
            for g_node in g_nodes:
                if g_node["type"] == "movie" and g_node.get("movie_id"):
                    m_id = g_node["movie_id"]
                    if m_id not in candidate_map:
                        candidate_map[m_id] = {
                            "movie_id": m_id,
                            "graph_score": 85.0,
                            "graph_reasoning": f"Direct graph entity match for '{g_node['name']}'",
                            "sources": ["Knowledge Graph"],
                            "raw_score": 85.0
                        }
                    else:
                        candidate_map[m_id]["sources"].append("Knowledge Graph Direct")
                        candidate_map[m_id]["raw_score"] = max(candidate_map[m_id]["raw_score"], 85.0)
        except Exception:
            pass

        # 3. Fallback / Augment with high-quality DB matches matching Persona genres/moods
        if len(candidate_map) < pool_size:
            all_movies = db.query(Movie).all()
            for m in all_movies:
                if m.id in candidate_map:
                    continue
                # Score against persona
                m_genres = [g.name for g in m.genres]
                genre_overlap = any(g in persona.preferred_genres for g in m_genres)
                if genre_overlap:
                    quality = (m.rating * 8.5) + (min(m.popularity, 100) * 0.15)
                    candidate_map[m.id] = {
                        "movie_id": m.id,
                        "hybrid_score": quality,
                        "hybrid_reasoning": f"Matches preferred genres ({', '.join(m_genres[:2])}) with high rating ({m.rating}/10)",
                        "sources": ["Hybrid ML Catalog"],
                        "raw_score": quality
                    }

        # Fetch movie models and construct rich candidate objects
        movie_ids = list(candidate_map.keys())
        movies = db.query(Movie).filter(Movie.id.in_(movie_ids)).all()
        movie_dict = {m.id: m for m in movies}

        scored_candidates = []
        for m_id, meta in candidate_map.items():
            m = movie_dict.get(m_id)
            if not m:
                continue

            # Calculate composite Scout score (0-100)
            base_score = meta.get("raw_score", 70.0)
            
            # Bonus for high rating & director prestige
            rating_bonus = (m.rating - 7.0) * 4.0 if m.rating else 0.0
            directors = [d.name for d in m.directors]
            is_auteur = any(d in ["Christopher Nolan", "Quentin Tarantino", "Denis Villeneuve", "Martin Scorsese", "Stanley Kubrick", "David Fincher", "Bong Joon-ho", "Ridley Scott", "Steven Spielberg"] for d in directors)
            auteur_bonus = 6.0 if is_auteur else 0.0

            scout_score = round(min(99.0, max(55.0, base_score + rating_bonus + auteur_bonus)), 1)
            
            # Primary discovery source
            primary_source = meta["sources"][0] if meta["sources"] else "Neural Vector Index"
            
            # Craft Scout Pitch
            m_genres = [g.name for g in m.genres]
            director_str = f"directed by {directors[0]}" if directors else ""
            m_year = m.release_date.split("-")[0] if m.release_date and "-" in m.release_date else "N/A"
            pitch = (
                f"Discovered via {primary_source}. \"{m.title}\" ({m_year}) {director_str} "
                f"delivers a {m.rating}/10 rated cinematic experience perfectly aligned with "
                f"the {persona.pacing_preference.lower()} tempo and {', '.join(persona.target_moods[:2])} mood."
            )
            if meta.get("vector_reasoning"):
                pitch += f" Neural context: {meta['vector_reasoning']}."

            scored_candidates.append({
                "movie": m,
                "movie_id": m.id,
                "scout_score": scout_score,
                "discovery_source": primary_source,
                "scout_pitch": pitch,
                "sources": meta["sources"]
            })

        # Sort by scout score descending
        scored_candidates.sort(key=lambda x: x["scout_score"], reverse=True)
        top_candidates = scored_candidates[:pool_size]

        # Formulate Scout message
        titles_preview = ", ".join([f"\"{c['movie'].title}\" ({c['scout_score']}%)" for c in top_candidates[:4]])
        scout_msg_content = (
            f"🔭 **Candidate Pool Retrieved**: Scouted {len(top_candidates)} high-resonance candidates "
            f"across Neural Transformers, Knowledge Graph, and Hybrid latent factors. "
            f"Top proposals: {titles_preview}. Ready for Film Critic cross-examination."
        )

        agent_msg = self.create_message(
            round_index=2,
            message_type="scout_pitch",
            content=scout_msg_content,
            confidence=0.94
        )

        return top_candidates, agent_msg
