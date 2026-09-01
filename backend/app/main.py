# backend/app/main.py
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.database.database import engine, Base, SessionLocal
from backend.app.api.movies import router as movies_router
from backend.app.api.auth import router as auth_router
from backend.app.api.watchlist import router as watchlist_router
from backend.app.api.ratings import router as ratings_router
from backend.app.api.ai import router as ai_router
from backend.app.api.recommendations import router as recommendations_router
from backend.app.api.semantic import router as semantic_router
from backend.app.api.graph import router as graph_router
from backend.app.services.hybrid_recommender import hybrid_engine
from backend.app.services.semantic_search import semantic_search_engine
from backend.app.services.graph_service import knowledge_graph_engine

# Configure loggers
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("movie_app")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing SQLite database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Train and initialize Phase 3, Phase 4 & Phase 5 ML / Vector / Graph models
    logger.info("Initializing ML models, Semantic Vector index & Cinematic Knowledge Graph...")
    db = SessionLocal()
    try:
        # Phase 3 Hybrid ML Engine
        stats = hybrid_engine.retrain_all(db)
        logger.info(f"Phase 3 ML Models initialized successfully: {stats}")
        
        # Phase 4 Semantic Vector Index
        semantic_ok = semantic_search_engine.fit(db)
        logger.info(f"Phase 4 Semantic Vector Engine initialized: {semantic_ok} ({len(semantic_search_engine.movie_ids)} vectors)")

        # Phase 5 Cinematic Knowledge Graph & GraphRAG Engine
        graph_ok = knowledge_graph_engine.build_graph(db)
        graph_stats = knowledge_graph_engine.get_graph_stats()
        logger.info(f"Phase 5 Knowledge Graph initialized: {graph_ok} ({graph_stats.get('total_nodes', 0)} nodes, {graph_stats.get('total_edges', 0)} edges)")
    except Exception as e:
        logger.error(f"Failed to initialize models on startup: {e}", exc_info=True)
    finally:
        db.close()

    logger.info("FastAPI Movie AI Platform startup complete.")
    yield
    logger.info("FastAPI Movie AI Platform shutting down.")

app = FastAPI(
    title="Movie AI Platform API",
    description="Enterprise Movie Discovery & Recommendation Platform Backend (Phase 5 Knowledge Graph & GraphRAG)",
    version="5.0.0",
    lifespan=lifespan
)

# Setup CORS for Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(movies_router)
app.include_router(auth_router)
app.include_router(watchlist_router)
app.include_router(ratings_router)
app.include_router(recommendations_router)
app.include_router(ai_router)
app.include_router(semantic_router)
app.include_router(graph_router)

@app.get("/", tags=["Health"])
def health_check():
    return {
        "status": "online",
        "service": "Movie AI Platform API",
        "version": "5.0.0",
        "docs_url": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)

