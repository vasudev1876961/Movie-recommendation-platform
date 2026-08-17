# backend/app/main.py
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.database.database import engine, Base
from backend.app.api.movies import router as movies_router

# Configure loggers
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("movie_app")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing SQLite database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("FastAPI Movie AI Platform startup complete.")
    yield
    logger.info("FastAPI Movie AI Platform shutting down.")

app = FastAPI(
    title="Movie AI Platform API",
    description="Enterprise Movie Discovery & Recommendation Platform Backend",
    version="2.0.0",
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

@app.get("/", tags=["Health"])
def health_check():
    return {
        "status": "online",
        "service": "Movie AI Platform API",
        "version": "2.0.0",
        "docs_url": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
