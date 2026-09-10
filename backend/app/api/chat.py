# backend/app/api/chat.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database.database import get_db
from backend.app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatHistoryResponse,
    ChatStartersResponse
)
from backend.app.services.chat.chat_engine import cine_copilot
from backend.app.services.chat.chat_session import chat_session_manager

router = APIRouter(prefix="/api/chat", tags=["Phase 7: CineCopilot Conversational AI"])

STARTER_PROMPTS = [
    {
        "category": "Streaming Availability",
        "prompt": "Where can I stream Inception right now?",
        "icon": "fa-film"
    },
    {
        "category": "Theme & Mood Discovery",
        "prompt": "Recommend mind-bending sci-fi movies where time or reality collapses",
        "icon": "fa-brain"
    },
    {
        "category": "Cinematic Showdown",
        "prompt": "Compare Inception and Interstellar side by side",
        "icon": "fa-scale-balanced"
    },
    {
        "category": "Critical Consensus",
        "prompt": "What do film critics think of Parasite?",
        "icon": "fa-award"
    },
    {
        "category": "Knowledge Graph Exploration",
        "prompt": "Show all movies directed by Christopher Nolan with high ratings",
        "icon": "fa-project-diagram"
    },
    {
        "category": "Pacing & Runtime Filter",
        "prompt": "Recommend gripping thrillers under 2 hours available on Netflix",
        "icon": "fa-clock"
    }
]

@router.post("/message", response_model=ChatResponse)
def post_chat_message(data: ChatRequest, db: Session = Depends(get_db)):
    """
    Submits a conversational message to CineCopilot.
    Maintains multi-turn dialogue history, coreference context, tool actions, and watch availability.
    """
    if not data.message or not data.message.strip():
        raise HTTPException(status_code=400, detail="Chat message cannot be empty")

    response = cine_copilot.process_message(
        message=data.message,
        session_id=data.session_id,
        db=db,
        region=data.region or "US",
        active_movie_id=data.active_movie_id
    )
    return response

@router.get("/history/{session_id}", response_model=ChatHistoryResponse)
def get_chat_history(session_id: str):
    """Retrieves conversation history and active candidate pool for a given session."""
    session = chat_session_manager.get_session(session_id)
    if not session:
        return ChatHistoryResponse(
            session_id=session_id,
            total_messages=0,
            messages=[],
            active_movie_pool=[]
        )

    return ChatHistoryResponse(
        session_id=session.session_id,
        total_messages=len(session.history),
        messages=session.history,
        active_movie_pool=[m.title for m in session.active_movie_pool]
    )

@router.delete("/session/{session_id}")
def clear_chat_session(session_id: str):
    """Resets conversational memory and clears the specified session."""
    success = chat_session_manager.clear_session(session_id)
    return {
        "session_id": session_id,
        "cleared": success,
        "message": "Session memory cleared successfully." if success else "Session not found."
    }

@router.get("/starters", response_model=ChatStartersResponse)
def get_chat_starters():
    """Provides curated starter prompts and icebreakers for CineCopilot."""
    return ChatStartersResponse(starters=STARTER_PROMPTS)
