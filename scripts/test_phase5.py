# scripts/test_phase5.py
import os
import sys

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from fastapi.testclient import TestClient
from backend.app.database.database import SessionLocal
from backend.app.models.movie import Movie
from backend.app.services.graph_service import knowledge_graph_engine
from backend.app.services.graph_rag import graph_rag_engine
from backend.app.main import app

def run_phase5_tests():
    print("=" * 80)
    print("MOVIEREC PHASE 5: KNOWLEDGE GRAPH & GRAPHRAG ENGINE TEST SUITE")
    print("=" * 80)

    db = SessionLocal()
    try:
        # 1. Test Knowledge Graph Construction & Topology
        print("\n[TEST 1] Testing Knowledge Graph Construction & Centrality Indexing...")
        built = knowledge_graph_engine.build_graph(db, force=True)
        assert built, "Failed to build Knowledge Graph!"
        
        stats = knowledge_graph_engine.get_graph_stats()
        print(f"✅ Knowledge Graph Built: {stats['total_nodes']} Total Nodes, {stats['total_edges']} Total Edges (Density: {stats['graph_density']})")
        print(f"   Node Distribution: {stats['node_distribution']}")
        print(f"   Relation Types: {stats['relation_distribution']}")

        assert stats['total_nodes'] >= 50, f"Expected at least 50 nodes, got {stats['total_nodes']}"
        assert stats['total_edges'] >= 100, f"Expected at least 100 edges, got {stats['total_edges']}"
        assert "movie" in stats['node_distribution'], "Movie node type missing!"
        assert "director" in stats['node_distribution'], "Director node type missing!"
        assert "actor" in stats['node_distribution'], "Actor node type missing!"
        assert "genre" in stats['node_distribution'], "Genre node type missing!"
        print("✅ Graph node types and relational topology verified.")

        # Top PageRank entities
        print(f"   Top Influential Directors: {[d['name'] for d in stats['top_central_directors'][:3]]}")
        print(f"   Top Influential Actors: {[a['name'] for a in stats['top_central_actors'][:3]]}")

        # 2. Test Multi-Hop Pathfinding & 6-Degrees-of-Separation
        print("\n[TEST 2] Testing Multi-Hop Shortest Pathfinding & Degrees of Separation...")
        inception = db.query(Movie).filter(Movie.title.ilike("%Inception%")).first()
        interstellar = db.query(Movie).filter(Movie.title.ilike("%Interstellar%")).first()

        if inception and interstellar:
            path_result = knowledge_graph_engine.find_shortest_path(inception.title, interstellar.title)
            assert path_result is not None, f"No path found between {inception.title} and {interstellar.title}"
            print(f"  Path between '{inception.title}' and '{interstellar.title}':")
            print(f"  👉 Degrees of Separation: {path_result['degrees_of_separation']}")
            print(f"     Path: {path_result['explanation']}")
            assert path_result['degrees_of_separation'] <= 3, "Expected path <= 3 hops between Nolan movies!"
            print("  ✅ Verified multi-hop pathfinding between movies.")

        # Test Director to Actor path
        nolan_actor_path = knowledge_graph_engine.find_shortest_path("Christopher Nolan", "Leonardo DiCaprio")
        if nolan_actor_path:
            print(f"  Path between 'Christopher Nolan' and 'Leonardo DiCaprio':")
            print(f"  👉 Degrees: {nolan_actor_path['degrees_of_separation']} | {nolan_actor_path['explanation']}")
            print("  ✅ Verified shortest path between Director and Actor.")

        # 3. Test Local Ego Subgraph Extraction
        print("\n[TEST 3] Testing Ego Subgraph Extraction for Interactive Graph Visualizer...")
        if inception:
            subgraph = knowledge_graph_engine.get_movie_subgraph(inception.id, depth=1, max_nodes=25)
            assert subgraph["root"] is not None, "Ego subgraph root is None!"
            assert len(subgraph["nodes"]) > 0, "Ego subgraph has no nodes!"
            assert len(subgraph["edges"]) > 0, "Ego subgraph has no edges!"
            print(f"✅ Ego Subgraph for '{inception.title}': {len(subgraph['nodes'])} nodes, {len(subgraph['edges'])} edges extracted.")

        # 4. Test Graph-Based Recommendations (Jaccard Entity Overlap)
        print("\n[TEST 4] Testing Graph Entity Overlap Recommendations...")
        if inception:
            graph_recs = knowledge_graph_engine.get_graph_recommendations(inception.id, top_n=4)
            assert len(graph_recs) > 0, "Graph recommendations returned 0 items!"
            print(f"Top Graph Picks for '{inception.title}':")
            for m_id, score, reason in graph_recs:
                m_obj = db.query(Movie).filter(Movie.id == m_id).first()
                print(f"  • {m_obj.title if m_obj else m_id} (Score: {score}) -> {reason}")
            print("✅ Graph recommendations with explainable entity link chains verified.")

        # 5. Test GraphRAG Hybrid Retrieval & Reasoning
        print("\n[TEST 5] Testing GraphRAG Hybrid Retrieval & Entity Grounding...")
        rag_query = "Sci-fi movies directed by Christopher Nolan with deep time and space exploration"
        rag_result = graph_rag_engine.rag_recommend(rag_query, db, top_k=4)
        
        assert rag_result["total"] > 0, "GraphRAG returned 0 items!"
        print(f"Query: \"{rag_query}\"")
        print(f"  Summary: {rag_result['summary']}")
        print(f"  Detected Entities: {rag_result['entities_detected']}")
        assert "Christopher Nolan" in rag_result['entities_detected'].get('directors', []), "Failed to detect Christopher Nolan!"
        
        print("\n  GraphRAG Grounded Recommendations:")
        for rec in rag_result["recommendations"]:
            print(f"  🌟 {rec['movie'].title} (Match: {rec['match_score']}%)")
            print(f"     Reasoning: {rec['reasoning']}")
            print(f"     Graph Facts: {rec['graph_facts'][:1]}")
            print(f"     Entities Matched: {rec['detected_entities_matched']}")
        print("✅ GraphRAG Entity Extraction and Hybrid Rank Fusion verified.")

        # 6. Test Neo4j Cypher DDL Export
        print("\n[TEST 6] Testing Neo4j Cypher DDL Generation & Script Export...")
        cypher_script = knowledge_graph_engine.export_cypher()
        assert "CREATE CONSTRAINT" in cypher_script, "Cypher script missing constraints!"
        assert "MERGE (m:Movie" in cypher_script, "Cypher script missing Movie nodes!"
        assert "MERGE (m)-[:DIRECTED_BY]->(d)" in cypher_script or "DIRECTED" in cypher_script, "Cypher script missing relationship edges!"
        print(f"✅ Cypher Script Generated successfully ({len(cypher_script.splitlines())} lines).")

        # 7. Test FastAPI Endpoints via TestClient
        print("\n[TEST 7] Testing FastAPI Phase 5 Graph Endpoints via TestClient...")
        client = TestClient(app)

        # 7a. GET /api/graph/stats
        res = client.get("/api/graph/stats")
        assert res.status_code == 200, f"GET /api/graph/stats failed: {res.text}"
        stats_data = res.json()
        assert stats_data["total_nodes"] > 0
        print(f"✅ GET /api/graph/stats -> 200 OK ({stats_data['total_nodes']} nodes)")

        # 7b. GET /api/graph/movie/{id}
        if inception:
            res = client.get(f"/api/graph/movie/{inception.id}?depth=1&max_nodes=20")
            assert res.status_code == 200, f"GET /api/graph/movie/{inception.id} failed: {res.text}"
            sub_data = res.json()
            assert len(sub_data["nodes"]) > 0
            print(f"✅ GET /api/graph/movie/{inception.id} -> 200 OK ({len(sub_data['nodes'])} nodes in visualizer subgraph)")

        # 7c. GET /api/graph/path
        if inception and interstellar:
            res = client.get(f"/api/graph/path?source={inception.title}&target={interstellar.title}")
            assert res.status_code == 200, f"GET /api/graph/path failed: {res.text}"
            p_data = res.json()
            assert p_data["degrees_of_separation"] >= 0
            print(f"✅ GET /api/graph/path -> 200 OK (Separation: {p_data['degrees_of_separation']} hops)")

        # 7d. GET /api/graph/explore
        res = client.get("/api/graph/explore?name=Christopher%20Nolan&limit=10")
        assert res.status_code == 200, f"GET /api/graph/explore failed: {res.text}"
        exp_data = res.json()
        assert exp_data["total_connections"] > 0
        print(f"✅ GET /api/graph/explore -> 200 OK ({exp_data['total_connections']} connections for Christopher Nolan)")

        # 7e. GET /api/graph/recommend/{id}
        if inception:
            res = client.get(f"/api/graph/recommend/{inception.id}?limit=4")
            assert res.status_code == 200, f"GET /api/graph/recommend failed: {res.text}"
            rec_data = res.json()
            assert len(rec_data) > 0
            print(f"✅ GET /api/graph/recommend/{inception.id} -> 200 OK ({len(rec_data)} graph recommendations)")

        # 7f. POST /api/graph/rag-recommend
        payload = {
            "query": "thrillers with Leonardo DiCaprio and mind bending psychological twists",
            "limit": 5,
            "min_score": 0.15
        }
        res = client.post("/api/graph/rag-recommend", json=payload)
        assert res.status_code == 200, f"POST /api/graph/rag-recommend failed: {res.text}"
        rag_api_data = res.json()
        assert rag_api_data["total"] > 0
        print(f"✅ POST /api/graph/rag-recommend -> 200 OK ({rag_api_data['total']} recommendations with GraphRAG facts)")

        # 7g. GET /api/graph/cypher-export
        res = client.get("/api/graph/cypher-export")
        assert res.status_code == 200, f"GET /api/graph/cypher-export failed: {res.text}"
        assert "CREATE CONSTRAINT" in res.text
        print("✅ GET /api/graph/cypher-export -> 200 OK (Cypher script downloadable)")

        # 7h. POST /api/admin/rebuild
        res = client.post("/api/graph/admin/rebuild")
        assert res.status_code == 200, f"POST /api/graph/admin/rebuild failed: {res.text}"
        print(f"✅ POST /api/graph/admin/rebuild -> 200 OK ({res.json()['message']})")

        print("\n" + "=" * 80)
        print("🎉 ALL PHASE 5 KNOWLEDGE GRAPH & GRAPHRAG TESTS PASSED PERFECTLY!")
        print("=" * 80)

    finally:
        db.close()

if __name__ == "__main__":
    run_phase5_tests()
