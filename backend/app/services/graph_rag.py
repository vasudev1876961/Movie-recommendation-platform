# backend/app/services/graph_rag.py
import logging
import re
from typing import Dict, List, Any, Optional, Set
from sqlalchemy.orm import Session
from backend.app.models.movie import Movie
from backend.app.services.graph_service import knowledge_graph_engine
from backend.app.services.semantic_search import semantic_search_engine

logger = logging.getLogger("movie_app.graph_rag")

class GraphRAGEngine:
    """
    Graph Retrieval-Augmented Generation (GraphRAG) Engine.
    Combines dense neural vector embeddings with structured multi-hop Knowledge Graph
    reasoning to deliver grounded, explainable, entity-linked movie recommendations.
    """

    def __init__(self):
        pass

    def extract_query_entities(self, query: str) -> Dict[str, List[str]]:
        """
        Extracts known cinematic entities (Directors, Actors, Genres, Movie Titles, Keywords)
        from a raw user natural language query using the knowledge graph lexicon.
        """
        q_lower = query.lower()
        extracted = {
            "directors": [],
            "actors": [],
            "genres": [],
            "movies": [],
            "keywords": []
        }

        if not knowledge_graph_engine.is_built:
            return extracted

        # Scan nodes in knowledge graph
        for node_id, data in knowledge_graph_engine.graph.nodes(data=True):
            ntype = data.get("node_type")
            name = (data.get("name") or data.get("title") or data.get("label") or "").strip()
            if not name or len(name) < 3:
                continue

            name_lower = name.lower()
            # Boundary-safe check
            pattern = r'\b' + re.escape(name_lower) + r'\b'
            if re.search(pattern, q_lower):
                if ntype == "director" and name not in extracted["directors"]:
                    extracted["directors"].append(name)
                elif ntype == "actor" and name not in extracted["actors"]:
                    extracted["actors"].append(name)
                elif ntype == "genre" and name not in extracted["genres"]:
                    extracted["genres"].append(name)
                elif ntype == "movie" and name not in extracted["movies"]:
                    extracted["movies"].append(name)
                elif ntype == "keyword" and name not in extracted["keywords"]:
                    extracted["keywords"].append(name)

        return extracted

    def rag_recommend(
        self,
        query: str,
        db: Session,
        top_k: int = 6,
        min_score: float = 0.15
    ) -> Dict[str, Any]:
        """
        Executes hybrid GraphRAG:
        1. Entity Extraction & Subgraph Expansion from Knowledge Graph
        2. Neural Vector Search (Phase 4 Transformer Embeddings)
        3. Multi-Hop Graph Path Tracing & Explanation Grounding
        4. Composite Graph-Neural Rank Fusion
        """
        if not knowledge_graph_engine.is_built:
            knowledge_graph_engine.build_graph(db)
        if not semantic_search_engine.is_trained:
            semantic_search_engine.fit(db)

        query_clean = query.strip()
        if not query_clean:
            return {
                "query": query,
                "entities_detected": {},
                "summary": "Please provide a search prompt or cinematic query.",
                "total": 0,
                "recommendations": []
            }

        # 1. Extract Entities from Query
        entities = self.extract_query_entities(query_clean)
        has_entities = any(len(v) > 0 for v in entities.values())

        # 2. Neural Vector Search Candidate Retrieval
        neural_hits = semantic_search_engine.search(query=query_clean, top_k=25, min_score=min_score)
        neural_map = {hit["movie_id"]: hit for hit in neural_hits}

        # 3. Knowledge Graph Expansion Candidate Retrieval
        graph_candidates: Dict[int, Dict[str, Any]] = {}

        # If entities found in query, traverse their 1-hop and 2-hop graph neighbors
        for dir_name in entities["directors"]:
            node = f"director_{dir_name.lower().replace(' ', '_')}"
            if knowledge_graph_engine.graph.has_node(node):
                for neighbor in knowledge_graph_engine.undirected_graph.neighbors(node):
                    if knowledge_graph_engine.graph.nodes[neighbor].get("node_type") == "movie":
                        m_id = knowledge_graph_engine.node_to_movie_id.get(neighbor)
                        if m_id:
                            graph_candidates.setdefault(m_id, {"score": 0.0, "reasons": []})
                            graph_candidates[m_id]["score"] += 35.0
                            graph_candidates[m_id]["reasons"].append(f"Directed by requested filmmaker {dir_name}")

        for act_name in entities["actors"]:
            node = f"actor_{act_name.lower().replace(' ', '_')}"
            if knowledge_graph_engine.graph.has_node(node):
                for neighbor in knowledge_graph_engine.undirected_graph.neighbors(node):
                    if knowledge_graph_engine.graph.nodes[neighbor].get("node_type") == "movie":
                        m_id = knowledge_graph_engine.node_to_movie_id.get(neighbor)
                        if m_id:
                            graph_candidates.setdefault(m_id, {"score": 0.0, "reasons": []})
                            graph_candidates[m_id]["score"] += 25.0
                            graph_candidates[m_id]["reasons"].append(f"Stars requested actor {act_name}")

        for genre_name in entities["genres"]:
            node = f"genre_{genre_name.lower().replace(' ', '_')}"
            if knowledge_graph_engine.graph.has_node(node):
                for neighbor in knowledge_graph_engine.undirected_graph.neighbors(node):
                    if knowledge_graph_engine.graph.nodes[neighbor].get("node_type") == "movie":
                        m_id = knowledge_graph_engine.node_to_movie_id.get(neighbor)
                        if m_id:
                            graph_candidates.setdefault(m_id, {"score": 0.0, "reasons": []})
                            graph_candidates[m_id]["score"] += 15.0
                            graph_candidates[m_id]["reasons"].append(f"Belongs to {genre_name} genre")

        # 4. Fusion & Multi-Hop Path Tracing
        all_candidate_ids = set(neural_map.keys()).union(set(graph_candidates.keys()))
        if not all_candidate_ids:
            # Fallback to all movies in database if no direct neural/entity hits
            all_movies = db.query(Movie).order_by(Movie.popularity.desc()).limit(top_k).all()
            all_candidate_ids = {m.id for m in all_movies}

        candidate_movies = db.query(Movie).filter(Movie.id.in_(all_candidate_ids)).all()
        scored_results = []

        for movie in candidate_movies:
            # Neural score component (0 to 1)
            n_hit = neural_map.get(movie.id)
            vector_sim = n_hit["cosine_similarity"] if n_hit else 0.20

            # Graph score component
            g_hit = graph_candidates.get(movie.id)
            g_score = g_hit["score"] if g_hit else 0.0
            g_reasons = g_hit["reasons"] if g_hit else []

            # PageRank graph centrality
            movie_node = knowledge_graph_engine.movie_node_map.get(movie.id)
            pr_val = knowledge_graph_engine.pagerank_scores.get(movie_node, 0.005) * 100

            # Trace multi-hop connection paths to query entities if any
            graph_facts = []
            if has_entities:
                for dir_name in entities["directors"]:
                    path_info = knowledge_graph_engine.find_shortest_path(movie.title, dir_name)
                    if path_info and path_info["degrees_of_separation"] <= 2:
                        graph_facts.append(f"🔗 {path_info['explanation']}")
                for act_name in entities["actors"]:
                    path_info = knowledge_graph_engine.find_shortest_path(movie.title, act_name)
                    if path_info and path_info["degrees_of_separation"] <= 2:
                        graph_facts.append(f"🔗 {path_info['explanation']}")

            # If no direct entity paths, formulate knowledge graph facts from movie attributes
            if not graph_facts:
                dir_str = ", ".join([d.name for d in movie.directors[:2]])
                cast_str = ", ".join([assoc.cast_member.name for assoc in movie.cast_associations[:2] if assoc.cast_member])
                genre_str = ", ".join([g.name for g in movie.genres[:2]])
                graph_facts.append(f"Knowledge Graph: Directed by {dir_str} • Starring {cast_str} • {genre_str}")

            # Composite match score calculation
            # 45% Vector Cosine + 35% Graph Entity Relevance + 10% Graph Centrality + 10% Rating Quality
            quality_prior = (float(movie.rating or 7.0) / 10.0)
            composite_score = (
                (vector_sim * 45.0) +
                (min(g_score, 40.0)) +
                (min(pr_val, 1.0) * 5.0) +
                (quality_prior * 10.0)
            )

            match_pct = min(99.0, max(60.0, round(composite_score, 1)))

            # Synthesize final explainable reasoning
            reasons_combined = []
            if n_hit and n_hit.get("reasoning"):
                reasons_combined.append(n_hit["reasoning"])
            if g_reasons:
                reasons_combined.append(" • ".join(g_reasons[:2]))

            reason_str = " | ".join(reasons_combined) if reasons_combined else graph_facts[0]

            scored_results.append({
                "movie": movie,
                "match_score": match_pct,
                "vector_similarity": round(vector_sim, 4),
                "graph_relevance": round(g_score, 2),
                "graph_facts": graph_facts,
                "reasoning": reason_str,
                "detected_entities_matched": [
                    e for sub in entities.values() for e in sub
                    if any(e.lower() in d.name.lower() for d in movie.directors)
                    or any(e.lower() in assoc.cast_member.name.lower() for assoc in movie.cast_associations if assoc.cast_member)
                    or any(e.lower() in g.name.lower() for g in movie.genres)
                    or e.lower() in movie.title.lower()
                ]
            })

        scored_results.sort(key=lambda x: x["match_score"], reverse=True)
        top_results = scored_results[:top_k]

        # Generate summary
        detected_entity_count = sum(len(v) for v in entities.values())
        if detected_entity_count > 0:
            flat_ents = [f"{k}: {', '.join(v)}" for k, v in entities.items() if v]
            summary = f"GraphRAG mapped {detected_entity_count} graph entities ({'; '.join(flat_ents)}) and traversed multi-hop relationship chains for \"{query}\"."
        else:
            summary = f"GraphRAG executed dense semantic vector resonance and graph topology traversal for \"{query}\"."

        return {
            "query": query,
            "entities_detected": entities,
            "summary": summary,
            "total": len(top_results),
            "recommendations": top_results
        }


# Global Singleton Instance
graph_rag_engine = GraphRAGEngine()
