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
from backend.app.api.agents import router as agents_router
from backend.app.api.streaming import router as streaming_router
from backend.app.api.chat import router as chat_router
from backend.app.api.trailers import router as trailers_router
from backend.app.api.watch_party import router as watch_party_router
from backend.app.api.studio import router as studio_router
from backend.app.api.spatial import router as spatial_router
from backend.app.services.hybrid_recommender import hybrid_engine
from backend.app.services.semantic_search import semantic_search_engine
from backend.app.services.graph_service import knowledge_graph_engine
from backend.app.services.agents.agent_orchestrator import agent_orchestrator
from backend.app.services.streaming_resolver import streaming_resolver
from backend.app.services.trailer_intelligence import trailer_intelligence
from backend.app.services.watch_party_service import watch_party_manager
from backend.app.services.neuro_studio import neuro_studio
from backend.app.services.spatial_biometrics import spatial_biometrics_service

# Configure loggers
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("movie_app")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing SQLite database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Train and initialize Phase 3, Phase 4, Phase 5, Phase 6 & Phase 7 engines
    logger.info("Initializing ML models, Semantic Vector index, Knowledge Graph, Multi-Agent Network & Streaming Resolver...")
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

        # Phase 6 Autonomous Multi-Agent Network
        roster = agent_orchestrator.get_roster()
        logger.info(f"Phase 6 Multi-Agent Network initialized: {len(roster)} agents active ({', '.join([a['name'] for a in roster])})")

        # Phase 7 Streaming Service Providers Resolver & CineCopilot
        providers = streaming_resolver.list_all_providers(db=db)
        logger.info(f"Phase 7 Streaming Resolver & CineCopilot initialized: {len(providers)} streaming platforms connected.")

        # Phase 8 Multimodal Trailer Intelligence & Watch Party Hub
        public_rooms = watch_party_manager.list_public_rooms()
        logger.info(f"Phase 8 Multimodal Trailer Intelligence & Real-Time Watch Parties initialized ({len(public_rooms)} active demo rooms).")

        # Phase 9 Neuro-Cinematic Generative Studio & LinguaCine Engine
        voices = neuro_studio.get_available_voices()
        vibes = neuro_studio.get_preset_vibes()
        logger.info(f"Phase 9 Neuro-Cinematic Studio & LinguaCine initialized: {len(voices)} voices, {len(vibes)} directorial vibes.")

        # Phase 10 CineSpatial AR 3D Theater & CinePulse Biometrics Engine
        envs = spatial_biometrics_service.get_environments()
        presets = spatial_biometrics_service.get_audio_presets()
        logger.info(f"Phase 10 CineSpatial AR & CinePulse initialized: {len(envs)} 3D environments, {len(presets)} binaural audio presets.")
    except Exception as e:
        logger.error(f"Failed to initialize models on startup: {e}", exc_info=True)
    finally:
        db.close()

    logger.info("FastAPI Movie AI Platform startup complete.")
    yield
    logger.info("FastAPI Movie AI Platform shutting down.")

app = FastAPI(
    title="Movie AI Platform API",
    description="Enterprise Movie Discovery & Recommendation Platform Backend (Phase 10 CineSpatial AR 3D Spatial Theater, CinePulse Biometrics & CineMesh Edge Mesh)",
    version="10.0.0",
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
app.include_router(agents_router)
app.include_router(streaming_router)
app.include_router(chat_router)
app.include_router(trailers_router)
app.include_router(watch_party_router)
app.include_router(studio_router)
app.include_router(spatial_router)

import os
from fastapi import Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Mount static asset folders if they exist
for folder in ["js", "css", "components", "data"]:
    folder_path = os.path.join(ROOT_DIR, folder)
    if os.path.exists(folder_path):
        app.mount(f"/{folder}", StaticFiles(directory=folder_path), name=folder)

@app.get("/api/tmdb.js", include_in_schema=False)
async def serve_tmdb_js():
    tmdb_path = os.path.join(ROOT_DIR, "api", "tmdb.js")
    if os.path.exists(tmdb_path):
        return FileResponse(tmdb_path, media_type="application/javascript")
    return JSONResponse({"error": "not found"}, status_code=404)

@app.get("/", tags=["Health"])
def health_or_index(request: Request):
    index_path = os.path.join(ROOT_DIR, "index.html")
    # If requested by a web browser, serve the single-page application
    if "text/html" in request.headers.get("accept", "") and os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    return {
        "status": "online",
        "service": "Movie AI Platform API",
        "version": "10.0.0",
        "docs_url": "/docs"
    }

@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "online",
        "service": "Movie AI Platform API",
        "version": "10.0.0",
        "docs_url": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=port, reload=True)

