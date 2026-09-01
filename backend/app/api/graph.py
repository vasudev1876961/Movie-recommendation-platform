# backend/app/api/graph.py
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from backend.app.database.database import get_db
from backend.app.models.movie import Movie
from backend.app.schemas.movie import MovieListItem
from backend.app.api.movies import format_movie_list_item
from backend.app.services.graph_service import knowledge_graph_engine
from backend.app.services.graph_rag import graph_rag_engine

router = APIRouter(prefix="/api/graph", tags=["Knowledge Graph & GraphRAG"])

# --- Schemas ---

class GraphNode(BaseModel):
    id: str
    label: str
    node_type: str
    name: Optional[str] = None
    title: Optional[str] = None
    rating: Optional[float] = None
    year: Optional[str] = None
    poster_path: Optional[str] = None
    val: Optional[float] = None

class GraphEdge(BaseModel):
    source: str
    target: str
    relation: str
    weight: Optional[float] = 1.0

class SubgraphResponse(BaseModel):
    root: Optional[str] = None
    total_nodes: int
    total_edges: int
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]

class PathFinderResponse(BaseModel):
    source: Dict[str, Any]
    target: Dict[str, Any]
    path_nodes: List[Dict[str, Any]]
    path_edges: List[Dict[str, Any]]
    degrees_of_separation: int
    explanation: str

class GraphRAGRequest(BaseModel):
    query: str
    limit: Optional[int] = 6
    min_score: Optional[float] = 0.15

class GraphRAGItem(BaseModel):
    movie: MovieListItem
    match_score: float
    vector_similarity: float
    graph_relevance: float
    graph_facts: List[str]
    reasoning: str
    detected_entities_matched: List[str]

class GraphRAGResponse(BaseModel):
    query: str
    entities_detected: Dict[str, List[str]]
    summary: str
    total: int
    recommendations: List[GraphRAGItem]

class GraphRecommendationItem(BaseModel):
    movie: MovieListItem
    graph_score: float
    reasoning: str

# --- Endpoints ---

@router.get("/stats")
def get_graph_statistics(db: Session = Depends(get_db)):
    """
    Returns topological statistics of the Cinematic Knowledge Graph,
    including node distributions, edge counts, density, and top central directors/actors.
    """
    if not knowledge_graph_engine.is_built:
        knowledge_graph_engine.build_graph(db)
    return knowledge_graph_engine.get_graph_stats()

@router.get("/movie/{movie_id}", response_model=SubgraphResponse)
def get_movie_subgraph(
    movie_id: int,
    depth: int = Query(1, ge=1, le=3),
    max_nodes: int = Query(35, ge=5, le=100),
    db: Session = Depends(get_db)
):
    """
    Extracts an ego subgraph centered around a specific movie
    for interactive node-link knowledge graph visualizers.
    """
    if not knowledge_graph_engine.is_built:
        knowledge_graph_engine.build_graph(db)

    subgraph = knowledge_graph_engine.get_movie_subgraph(movie_id, depth=depth, max_nodes=max_nodes)
    if not subgraph.get("root"):
        raise HTTPException(status_code=404, detail=f"Movie with ID {movie_id} not found in Knowledge Graph")

    return subgraph

@router.get("/path", response_model=PathFinderResponse)
def find_cinematic_path(
    source: str = Query(..., description="Source movie, director, actor, or genre"),
    target: str = Query(..., description="Target movie, director, actor, or genre"),
    db: Session = Depends(get_db)
):
    """
    Calculates the shortest multi-hop connection path (degrees of separation)
    between any two cinematic entities (e.g. Inception ↔ Interstellar, or Christopher Nolan ↔ Leonardo DiCaprio).
    """
    if not knowledge_graph_engine.is_built:
        knowledge_graph_engine.build_graph(db)

    path_data = knowledge_graph_engine.find_shortest_path(source, target)
    if not path_data:
        raise HTTPException(
            status_code=404,
            detail=f"No cinematic connection path found between '{source}' and '{target}'"
        )

    return path_data

@router.get("/explore")
def explore_entity_neighborhood(
    name: str = Query(..., description="Name of director, actor, genre, or movie"),
    entity_type: Optional[str] = Query("all", description="Filter by entity type"),
    limit: int = Query(15, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Explores the immediate neighborhood, connected filmography, and collaborations for an entity.
    """
    if not knowledge_graph_engine.is_built:
        knowledge_graph_engine.build_graph(db)

    result = knowledge_graph_engine.get_entity_neighborhood(entity_type, name, limit=limit)
    if not result.get("entity"):
        raise HTTPException(status_code=404, detail=f"Entity '{name}' not found in Knowledge Graph")

    return result

@router.get("/recommend/{movie_id}", response_model=List[GraphRecommendationItem])
def get_graph_recommendations(
    movie_id: int,
    limit: int = Query(6, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """
    Returns graph-based recommendations using multi-hop entity co-occurrence and Jaccard scoring.
    """
    if not knowledge_graph_engine.is_built:
        knowledge_graph_engine.build_graph(db)

    raw_recs = knowledge_graph_engine.get_graph_recommendations(movie_id, top_n=limit)
    if not raw_recs:
        return []

    movie_ids = [m_id for m_id, _, _ in raw_recs]
    movies = db.query(Movie).filter(Movie.id.in_(movie_ids)).all()
    movie_map = {m.id: m for m in movies}

    results = []
    for m_id, score, reason in raw_recs:
        m = movie_map.get(m_id)
        if m:
            results.append(GraphRecommendationItem(
                movie=format_movie_list_item(m),
                graph_score=score,
                reasoning=reason
            ))

    return results

@router.post("/rag-recommend", response_model=GraphRAGResponse)
def rag_recommend(
    payload: GraphRAGRequest,
    db: Session = Depends(get_db)
):
    """
    Executes hybrid GraphRAG:
    Entity Extraction -> Knowledge Graph Subgraph Expansion -> Dense Vector Search -> Multi-hop Reasoning.
    """
    rag_data = graph_rag_engine.rag_recommend(
        query=payload.query,
        db=db,
        top_k=payload.limit or 6,
        min_score=payload.min_score or 0.15
    )

    formatted_recs = []
    for item in rag_data["recommendations"]:
        formatted_recs.append(GraphRAGItem(
            movie=format_movie_list_item(item["movie"]),
            match_score=item["match_score"],
            vector_similarity=item["vector_similarity"],
            graph_relevance=item["graph_relevance"],
            graph_facts=item["graph_facts"],
            reasoning=item["reasoning"],
            detected_entities_matched=item["detected_entities_matched"]
        ))

    return GraphRAGResponse(
        query=rag_data["query"],
        entities_detected=rag_data["entities_detected"],
        summary=rag_data["summary"],
        total=rag_data["total"],
        recommendations=formatted_recs
    )

@router.get("/cypher-export")
def export_cypher_script(db: Session = Depends(get_db)):
    """
    Generates downloadable Neo4j Cypher DDL and batch MERGE script
    for exporting the knowledge graph into Neo4j 5.x / Neo4j Desktop / AuraDB.
    """
    if not knowledge_graph_engine.is_built:
        knowledge_graph_engine.build_graph(db)

    cypher_script = knowledge_graph_engine.export_cypher()
    return Response(
        content=cypher_script,
        media_type="text/plain",
        headers={"Content-Disposition": "attachment; filename=movierec_knowledge_graph.cypher"}
    )

@router.post("/admin/rebuild")
def rebuild_knowledge_graph(db: Session = Depends(get_db)):
    """Forces complete rebuild of the Knowledge Graph and centrality indexes."""
    ok = knowledge_graph_engine.build_graph(db, force=True)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to rebuild knowledge graph")
    stats = knowledge_graph_engine.get_graph_stats()
    return {
        "status": "success",
        "message": f"Successfully built Knowledge Graph with {stats['total_nodes']} nodes and {stats['total_edges']} edges.",
        "stats": stats
    }
