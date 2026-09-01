# backend/app/services/graph_service.py
import logging
import re
from typing import Dict, List, Any, Optional, Tuple, Set
import networkx as nx
from sqlalchemy.orm import Session
from backend.app.models.movie import Movie, Genre, Director, CastMember

logger = logging.getLogger("movie_app.graph")

class KnowledgeGraphEngine:
    """
    Enterprise Cinematic Knowledge Graph Engine.
    Builds a multi-relational property graph connecting Movies, Directors, Actors, Genres, and Keywords.
    Provides sub-graph extraction, multi-hop pathfinding, PageRank centrality, and Neo4j Cypher generation.
    """

    def __init__(self):
        # We maintain a directed MultiDiGraph for relational semantics and an undirected Graph for fast pathfinding
        self.graph: nx.MultiDiGraph = nx.MultiDiGraph()
        self.undirected_graph: nx.Graph = nx.Graph()
        self.is_built: bool = False
        
        # Entity lookups
        self.movie_node_map: Dict[int, str] = {} # movie_id -> node_id (e.g. "movie_1")
        self.node_to_movie_id: Dict[str, int] = {}
        self.entity_name_to_node: Dict[str, str] = {} # lower(name) -> node_id

        # Centrality cache
        self.pagerank_scores: Dict[str, float] = {}
        self.top_directors: List[Dict[str, Any]] = []
        self.top_actors: List[Dict[str, Any]] = []
        self.top_genres: List[Dict[str, Any]] = []

    def build_graph(self, db: Session, force: bool = False) -> bool:
        """
        Builds the entire cinematic knowledge graph from SQLite database.
        """
        if self.is_built and not force:
            return True

        logger.info("Constructing Cinematic Knowledge Graph from database...")
        g = nx.MultiDiGraph()
        ug = nx.Graph()

        self.movie_node_map.clear()
        self.node_to_movie_id.clear()
        self.entity_name_to_node.clear()

        movies = db.query(Movie).all()
        if not movies:
            logger.warning("No movies found in database to build Knowledge Graph.")
            return False

        # 1. Ingest Movie Nodes
        for m in movies:
            movie_node = f"movie_{m.id}"
            self.movie_node_map[m.id] = movie_node
            self.node_to_movie_id[movie_node] = m.id
            self.entity_name_to_node[m.title.lower().strip()] = movie_node

            year = ""
            if m.release_date and len(m.release_date) >= 4:
                year = m.release_date[:4]

            movie_attrs = {
                "id": m.id,
                "node_type": "movie",
                "label": m.title,
                "title": m.title,
                "rating": float(m.rating or 0.0),
                "year": year,
                "popularity": float(m.popularity or 0.0),
                "poster_path": m.poster_path or "",
                "vote_count": int(m.vote_count or 0),
                "overview": m.overview or ""
            }
            g.add_node(movie_node, **movie_attrs)
            ug.add_node(movie_node, **movie_attrs)

            # 2. Ingest Genres & Edges
            for genre in m.genres:
                genre_node = f"genre_{genre.name.lower().replace(' ', '_')}"
                if not g.has_node(genre_node):
                    genre_attrs = {
                        "id": genre_node,
                        "node_type": "genre",
                        "label": genre.name,
                        "name": genre.name
                    }
                    g.add_node(genre_node, **genre_attrs)
                    ug.add_node(genre_node, **genre_attrs)
                    self.entity_name_to_node[genre.name.lower().strip()] = genre_node

                g.add_edge(movie_node, genre_node, relation="IN_GENRE", weight=1.0)
                g.add_edge(genre_node, movie_node, relation="GENRE_OF", weight=1.0)
                ug.add_edge(movie_node, genre_node, relation="IN_GENRE", weight=1.0)

            # 3. Ingest Directors & Edges
            for director in m.directors:
                dir_name_clean = director.name.strip()
                if not dir_name_clean:
                    continue
                dir_node = f"director_{dir_name_clean.lower().replace(' ', '_')}"
                if not g.has_node(dir_node):
                    dir_attrs = {
                        "id": dir_node,
                        "node_type": "director",
                        "label": dir_name_clean,
                        "name": dir_name_clean
                    }
                    g.add_node(dir_node, **dir_attrs)
                    ug.add_node(dir_node, **dir_attrs)
                    self.entity_name_to_node[dir_name_clean.lower()] = dir_node

                g.add_edge(movie_node, dir_node, relation="DIRECTED_BY", weight=2.0)
                g.add_edge(dir_node, movie_node, relation="DIRECTED", weight=2.0)
                ug.add_edge(movie_node, dir_node, relation="DIRECTED_BY", weight=2.0)

            # 4. Ingest Actors (Top 6 cast members per movie)
            for assoc in m.cast_associations[:6]:
                if not assoc.cast_member:
                    continue
                actor_name = assoc.cast_member.name.strip()
                if not actor_name:
                    continue
                actor_node = f"actor_{actor_name.lower().replace(' ', '_')}"
                if not g.has_node(actor_node):
                    actor_attrs = {
                        "id": actor_node,
                        "node_type": "actor",
                        "label": actor_name,
                        "name": actor_name
                    }
                    g.add_node(actor_node, **actor_attrs)
                    ug.add_node(actor_node, **actor_attrs)
                    self.entity_name_to_node[actor_name.lower()] = actor_node

                cast_weight = 1.8 if assoc.cast_order < 3 else 1.2
                g.add_edge(movie_node, actor_node, relation="STARS", character=assoc.character or "", order=assoc.cast_order, weight=cast_weight)
                g.add_edge(actor_node, movie_node, relation="ACTED_IN", character=assoc.character or "", order=assoc.cast_order, weight=cast_weight)
                ug.add_edge(movie_node, actor_node, relation="STARS", weight=cast_weight)

            # 5. Ingest Keywords (Clean top keywords)
            if m.keywords:
                raw_kw = [k.strip().lower() for k in re.split(r'[,|;]', m.keywords) if k.strip()]
                for kw in raw_kw[:5]:
                    if len(kw) < 3:
                        continue
                    kw_node = f"keyword_{kw.replace(' ', '_')}"
                    if not g.has_node(kw_node):
                        kw_attrs = {
                            "id": kw_node,
                            "node_type": "keyword",
                            "label": kw.title(),
                            "name": kw
                        }
                        g.add_node(kw_node, **kw_attrs)
                        ug.add_node(kw_node, **kw_attrs)
                        self.entity_name_to_node[kw] = kw_node

                    g.add_edge(movie_node, kw_node, relation="HAS_KEYWORD", weight=0.8)
                    g.add_edge(kw_node, movie_node, relation="KEYWORD_OF", weight=0.8)
                    ug.add_edge(movie_node, kw_node, relation="HAS_KEYWORD", weight=0.8)

        # 6. Add High-Order Direct Collaboration Edges between Directors & Cast
        for m in movies:
            movie_directors = [d.name.strip() for d in m.directors if d.name.strip()]
            movie_actors = [assoc.cast_member.name.strip() for assoc in m.cast_associations[:5] if assoc.cast_member and assoc.cast_member.name.strip()]

            for dir_name in movie_directors:
                dir_node = f"director_{dir_name.lower().replace(' ', '_')}"
                for act_name in movie_actors:
                    act_node = f"actor_{act_name.lower().replace(' ', '_')}"
                    if g.has_node(dir_node) and g.has_node(act_node):
                        if not ug.has_edge(dir_node, act_node):
                            g.add_edge(dir_node, act_node, relation="COLLABORATED_WITH", movie=m.title, weight=1.5)
                            g.add_edge(act_node, dir_node, relation="COLLABORATED_WITH", movie=m.title, weight=1.5)
                            ug.add_edge(dir_node, act_node, relation="COLLABORATED_WITH", weight=1.5)

            # Actor co-star edges
            for i, act1 in enumerate(movie_actors):
                node1 = f"actor_{act1.lower().replace(' ', '_')}"
                for act2 in movie_actors[i+1:]:
                    node2 = f"actor_{act2.lower().replace(' ', '_')}"
                    if g.has_node(node1) and g.has_node(node2):
                        if not ug.has_edge(node1, node2):
                            g.add_edge(node1, node2, relation="CO_STARRED_WITH", movie=m.title, weight=1.0)
                            g.add_edge(node2, node1, relation="CO_STARRED_WITH", movie=m.title, weight=1.0)
                            ug.add_edge(node1, node2, relation="CO_STARRED_WITH", weight=1.0)

        self.graph = g
        self.undirected_graph = ug
        self.is_built = True

        # Compute PageRank and Centrality metrics
        self._compute_centrality()

        logger.info(
            f"✅ Knowledge Graph constructed: {g.number_of_nodes()} nodes, {g.number_of_edges()} edges "
            f"({len(self.movie_node_map)} movies)."
        )
        return True

    def _compute_centrality(self):
        """Calculates PageRank & Degree Centrality across the entire graph."""
        try:
            pr = nx.pagerank(self.undirected_graph, alpha=0.85, max_iter=100)
            self.pagerank_scores = pr

            # Top central directors
            directors = [
                {"name": data.get("name", node), "score": round(pr[node] * 1000, 3), "degree": self.undirected_graph.degree(node)}
                for node, data in self.graph.nodes(data=True)
                if data.get("node_type") == "director" and node in pr
            ]
            directors.sort(key=lambda x: x["score"], reverse=True)
            self.top_directors = directors[:10]

            # Top central actors
            actors = [
                {"name": data.get("name", node), "score": round(pr[node] * 1000, 3), "degree": self.undirected_graph.degree(node)}
                for node, data in self.graph.nodes(data=True)
                if data.get("node_type") == "actor" and node in pr
            ]
            actors.sort(key=lambda x: x["score"], reverse=True)
            self.top_actors = actors[:10]

            # Top central genres
            genres = [
                {"name": data.get("name", node), "score": round(pr[node] * 1000, 3), "degree": self.undirected_graph.degree(node)}
                for node, data in self.graph.nodes(data=True)
                if data.get("node_type") == "genre" and node in pr
            ]
            genres.sort(key=lambda x: x["score"], reverse=True)
            self.top_genres = genres[:10]

        except Exception as e:
            logger.warning(f"Failed to compute PageRank: {e}")

    def get_movie_subgraph(self, movie_id: int, depth: int = 1, max_nodes: int = 35) -> Dict[str, Any]:
        """
        Extracts a localized ego subgraph around a movie for interactive frontend visualization.
        """
        movie_node = self.movie_node_map.get(movie_id)
        if not movie_node or not self.graph.has_node(movie_node):
            return {"nodes": [], "edges": [], "root": None}

        # BFS ego graph extraction
        visited_nodes: Set[str] = {movie_node}
        current_layer: Set[str] = {movie_node}

        for _ in range(depth):
            next_layer: Set[str] = set()
            for n in current_layer:
                neighbors = list(self.undirected_graph.neighbors(n))
                for neighbor in neighbors:
                    if len(visited_nodes) < max_nodes:
                        visited_nodes.add(neighbor)
                        next_layer.add(neighbor)
            current_layer = next_layer
            if len(visited_nodes) >= max_nodes:
                break

        # Also pull sibling movies that share director or main star
        directors = [nbr for nbr in self.undirected_graph.neighbors(movie_node) if self.graph.nodes[nbr].get("node_type") == "director"]
        for d_node in directors:
            for sibling in self.undirected_graph.neighbors(d_node):
                if self.graph.nodes[sibling].get("node_type") == "movie" and len(visited_nodes) < max_nodes:
                    visited_nodes.add(sibling)

        sub_g = self.graph.subgraph(visited_nodes)

        nodes_data = []
        for n in sub_g.nodes():
            attrs = dict(self.graph.nodes[n])
            attrs["id"] = n
            attrs["val"] = self.pagerank_scores.get(n, 0.01) * 100
            nodes_data.append(attrs)

        edges_data = []
        seen_edges = set()
        for u, v, k, data in sub_g.edges(keys=True, data=True):
            edge_key = tuple(sorted([u, v])) + (data.get("relation", "RELATED"),)
            if edge_key not in seen_edges:
                seen_edges.add(edge_key)
                edges_data.append({
                    "source": u,
                    "target": v,
                    "relation": data.get("relation", "CONNECTED_TO"),
                    "weight": data.get("weight", 1.0)
                })

        return {
            "root": movie_node,
            "total_nodes": len(nodes_data),
            "total_edges": len(edges_data),
            "nodes": nodes_data,
            "edges": edges_data
        }

    def find_shortest_path(self, source_query: str, target_query: str) -> Optional[Dict[str, Any]]:
        """
        Calculates the degrees of separation and shortest cinematic relation path
        between any two entities (Movies, Directors, Actors, Genres).
        """
        src_node = self._resolve_entity_node(source_query)
        tgt_node = self._resolve_entity_node(target_query)

        if not src_node or not tgt_node:
            return None

        if src_node == tgt_node:
            return {
                "source": self.graph.nodes[src_node],
                "target": self.graph.nodes[tgt_node],
                "path_nodes": [self.graph.nodes[src_node]],
                "path_edges": [],
                "degrees_of_separation": 0,
                "explanation": "Both entities are identical."
            }

        try:
            path = nx.shortest_path(self.undirected_graph, source=src_node, target=tgt_node)
            path_nodes = [dict(self.graph.nodes[n], id=n) for n in path]
            path_edges = []
            explanation_parts = []

            for i in range(len(path) - 1):
                u, v = path[i], path[i+1]
                edge_data = self.graph.get_edge_data(u, v) or self.graph.get_edge_data(v, u) or {}
                rel = "CONNECTED_TO"
                if edge_data:
                    # Pick first edge key
                    first_key = list(edge_data.keys())[0]
                    rel = edge_data[first_key].get("relation", "CONNECTED_TO")

                path_edges.append({
                    "source": u,
                    "target": v,
                    "relation": rel
                })

                u_label = self.graph.nodes[u].get("label", u)
                v_label = self.graph.nodes[v].get("label", v)
                u_type = self.graph.nodes[u].get("node_type", "entity")
                v_type = self.graph.nodes[v].get("node_type", "entity")

                # Build readable step
                if rel == "DIRECTED_BY" or rel == "DIRECTED":
                    explanation_parts.append(f"{u_label} is directed by {v_label}" if u_type == "movie" else f"{u_label} directed {v_label}")
                elif rel == "STARS" or rel == "ACTED_IN":
                    explanation_parts.append(f"{u_label} stars {v_label}" if u_type == "movie" else f"{u_label} starred in {v_label}")
                elif rel == "COLLABORATED_WITH":
                    explanation_parts.append(f"{u_label} collaborated with {v_label}")
                elif rel == "CO_STARRED_WITH":
                    explanation_parts.append(f"{u_label} co-starred with {v_label}")
                elif rel == "IN_GENRE" or rel == "GENRE_OF":
                    explanation_parts.append(f"{u_label} is categorized in {v_label}" if u_type == "movie" else f"{u_label} features {v_label}")
                else:
                    explanation_parts.append(f"{u_label} ──[{rel}]──► {v_label}")

            explanation = " ➔ ".join(explanation_parts)

            return {
                "source": dict(self.graph.nodes[src_node], id=src_node),
                "target": dict(self.graph.nodes[tgt_node], id=tgt_node),
                "path_nodes": path_nodes,
                "path_edges": path_edges,
                "degrees_of_separation": len(path) - 1,
                "explanation": explanation
            }
        except nx.NetworkXNoPath:
            return None
        except Exception as e:
            logger.error(f"Error finding shortest path between {source_query} and {target_query}: {e}")
            return None

    def get_entity_neighborhood(self, entity_type: str, entity_name: str, limit: int = 15) -> Dict[str, Any]:
        """
        Retrieves direct connected filmography, collaborating peers, and genres for an entity.
        """
        node_id = self._resolve_entity_node(entity_name)
        if not node_id or not self.graph.has_node(node_id):
            return {"entity": None, "connections": []}

        entity_attrs = dict(self.graph.nodes[node_id], id=node_id)
        connections = []

        for neighbor in self.undirected_graph.neighbors(node_id):
            nbr_attrs = dict(self.graph.nodes[neighbor], id=neighbor)
            edge_data = self.graph.get_edge_data(node_id, neighbor) or self.graph.get_edge_data(neighbor, node_id) or {}
            rel = "CONNECTED"
            if edge_data:
                first_k = list(edge_data.keys())[0]
                rel = edge_data[first_k].get("relation", "CONNECTED")

            connections.append({
                "node": nbr_attrs,
                "relation": rel
            })

        # Sort: movies by rating, people by PageRank
        connections.sort(
            key=lambda x: x["node"].get("rating", 0.0) if x["node"].get("node_type") == "movie" else self.pagerank_scores.get(x["node"]["id"], 0.0),
            reverse=True
        )

        return {
            "entity": entity_attrs,
            "total_connections": len(connections),
            "connections": connections[:limit]
        }

    def get_graph_recommendations(self, movie_id: int, top_n: int = 6) -> List[Tuple[int, float, str]]:
        """
        Graph-based multi-hop recommendation using Jaccard entity overlap and random walk co-occurrence.
        Returns: [(candidate_movie_id, graph_match_score, graph_reasoning_string)]
        """
        source_node = self.movie_node_map.get(movie_id)
        if not source_node or not self.graph.has_node(source_node):
            return []

        source_title = self.graph.nodes[source_node].get("title", "")
        # Get source entity neighbors (directors, actors, genres, keywords)
        source_neighbors = set(self.undirected_graph.neighbors(source_node))

        candidate_scores: Dict[str, Dict[str, Any]] = {}

        for nbr in source_neighbors:
            nbr_type = self.graph.nodes[nbr].get("node_type")
            nbr_label = self.graph.nodes[nbr].get("label", nbr)

            # Weight by entity type significance
            type_weight = {
                "director": 4.5,
                "actor": 3.0,
                "genre": 1.5,
                "keyword": 1.8
            }.get(nbr_type, 1.0)

            # Look at movies connected to this neighbor
            for candidate_node in self.undirected_graph.neighbors(nbr):
                if candidate_node == source_node:
                    continue
                if self.graph.nodes[candidate_node].get("node_type") != "movie":
                    continue

                if candidate_node not in candidate_scores:
                    candidate_scores[candidate_node] = {
                        "score": 0.0,
                        "shared_entities": [],
                        "movie_id": self.node_to_movie_id.get(candidate_node)
                    }

                candidate_scores[candidate_node]["score"] += type_weight
                candidate_scores[candidate_node]["shared_entities"].append(f"{nbr_type.capitalize()}: {nbr_label}")

        # Compute Jaccard entity coefficient for refinement
        results = []
        for c_node, c_data in candidate_scores.items():
            c_neighbors = set(self.undirected_graph.neighbors(c_node))
            intersection = len(source_neighbors.intersection(c_neighbors))
            union = len(source_neighbors.union(c_neighbors))
            jaccard = (intersection / union) if union > 0 else 0.0

            # Quality prior
            c_rating = self.graph.nodes[c_node].get("rating", 7.0)
            final_score = c_data["score"] + (jaccard * 10.0) + (c_rating * 0.5)

            # Format human reasoning
            entities_str = ", ".join(c_data["shared_entities"][:3])
            reasoning = f"2-Hop Graph Link: Connected with {source_title} via shared {entities_str}"

            if c_data["movie_id"]:
                results.append((c_data["movie_id"], round(final_score, 2), reasoning))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_n]

    def get_graph_stats(self) -> Dict[str, Any]:
        """Returns topological statistics of the Cinematic Knowledge Graph."""
        if not self.is_built:
            return {"is_built": False}

        type_counts: Dict[str, int] = {}
        for _, data in self.graph.nodes(data=True):
            t = data.get("node_type", "other")
            type_counts[t] = type_counts.get(t, 0) + 1

        rel_counts: Dict[str, int] = {}
        for _, _, data in self.graph.edges(data=True):
            r = data.get("relation", "OTHER")
            rel_counts[r] = rel_counts.get(r, 0) + 1

        density = nx.density(self.undirected_graph)

        return {
            "is_built": True,
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "graph_density": round(density, 6),
            "node_distribution": type_counts,
            "relation_distribution": rel_counts,
            "top_central_directors": self.top_directors,
            "top_central_actors": self.top_actors,
            "top_central_genres": self.top_genres
        }

    def export_cypher(self) -> str:
        """
        Generates Neo4j Cypher DDL and Batch CREATE/MERGE script
        allowing export to any Neo4j 5.x / AuraDB cluster.
        """
        lines = [
            "// ========================================================",
            "// MOVIEREC PHASE 5: CINEMATIC KNOWLEDGE GRAPH CYPHER DDL",
            "// Compatible with Neo4j 5.x, Neo4j Desktop & Neo4j AuraDB",
            "// ========================================================\n",
            "// Constraints & Indexes",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (m:Movie) REQUIRE m.id IS UNIQUE;",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Director) REQUIRE d.name IS UNIQUE;",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (a:Actor) REQUIRE a.name IS UNIQUE;",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (g:Genre) REQUIRE g.name IS UNIQUE;\n"
        ]

        # Export Nodes
        lines.append("// Ingest Nodes")
        for node_id, data in self.graph.nodes(data=True):
            ntype = data.get("node_type", "Entity")
            if ntype == "movie":
                safe_title = data.get('title', '').replace("'", "\\'")
                lines.append(
                    f"MERGE (m:Movie {{id: {data.get('id')}}}) "
                    f"SET m.title = '{safe_title}', m.rating = {data.get('rating', 0.0)}, "
                    f"m.year = '{data.get('year', '')}', m.popularity = {data.get('popularity', 0.0)};"
                )
            elif ntype == "director":
                safe_name = data.get('name', '').replace("'", "\\'")
                lines.append(f"MERGE (d:Director {{name: '{safe_name}'}});")
            elif ntype == "actor":
                safe_name = data.get('name', '').replace("'", "\\'")
                lines.append(f"MERGE (a:Actor {{name: '{safe_name}'}});")
            elif ntype == "genre":
                safe_name = data.get('name', '').replace("'", "\\'")
                lines.append(f"MERGE (g:Genre {{name: '{safe_name}'}});")

        # Export Edges
        lines.append("\n// Ingest Relationships")
        for u, v, data in self.graph.edges(data=True):
            u_data = self.graph.nodes[u]
            v_data = self.graph.nodes[v]
            rel = data.get("relation", "CONNECTED_TO")

            if rel == "DIRECTED_BY" and u_data.get("node_type") == "movie" and v_data.get("node_type") == "director":
                safe_dir = v_data.get('name', '').replace("'", "\\'")
                lines.append(f"MATCH (m:Movie {{id: {u_data.get('id')}}}), (d:Director {{name: '{safe_dir}'}}) MERGE (m)-[:DIRECTED_BY]->(d);")
            elif rel == "STARS" and u_data.get("node_type") == "movie" and v_data.get("node_type") == "actor":
                safe_actor = v_data.get('name', '').replace("'", "\\'")
                lines.append(f"MATCH (m:Movie {{id: {u_data.get('id')}}}), (a:Actor {{name: '{safe_actor}'}}) MERGE (m)-[:STARS]->(a);")
            elif rel == "IN_GENRE" and u_data.get("node_type") == "movie" and v_data.get("node_type") == "genre":
                safe_genre = v_data.get('name', '').replace("'", "\\'")
                lines.append(f"MATCH (m:Movie {{id: {u_data.get('id')}}}), (g:Genre {{name: '{safe_genre}'}}) MERGE (m)-[:IN_GENRE]->(g);")

        return "\n".join(lines)

    def _resolve_entity_node(self, query: str) -> Optional[str]:
        """Resolves natural language or ID queries to exact graph node IDs."""
        if not query:
            return None
        q = str(query).strip()

        # If already node id format
        if q in self.graph:
            return q

        # If numeric movie ID
        if q.isdigit():
            m_id = int(q)
            if m_id in self.movie_node_map:
                return self.movie_node_map[m_id]

        q_lower = q.lower()
        if q_lower in self.entity_name_to_node:
            return self.entity_name_to_node[q_lower]

        # Partial substring matching
        for name, node_id in self.entity_name_to_node.items():
            if q_lower in name or name in q_lower:
                return node_id

        return None


# Global Singleton Instance
knowledge_graph_engine = KnowledgeGraphEngine()
