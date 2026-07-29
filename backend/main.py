import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import check_db_connection
from backend.routers import auth, users, movies, watchlist, recommendations

# Configure loggers
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn.error")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Perform database connectivity checks on startup
    await check_db_connection()
    yield
    # Cleanup database connection clients if needed on shutdown

app = FastAPI(
    title="MovieRec API Platform",
    description="FastAPI Backend for Movie Recommendation Engine",
    version="1.0.0",
    lifespan=lifespan
)

# Setup CORS middleware for local frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register endpoints routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(movies.router)
app.include_router(watchlist.router)
app.include_router(recommendations.router)

@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "MovieRec Backend API is running."
    }
