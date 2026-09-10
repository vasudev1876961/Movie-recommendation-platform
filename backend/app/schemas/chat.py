# backend/app/schemas/chat.py
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from backend.app.schemas.movie import MovieListItem
from backend.app.schemas.streaming import MovieStreamingAvailability

class ChatMessage(BaseModel):
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: Optional[str] = None
    movies: Optional[List[MovieListItem]] = None
    streaming_options: Optional[Dict[int, MovieStreamingAvailability]] = None
    suggested_followups: Optional[List[str]] = None

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    region: Optional[str] = "US"
    active_movie_id: Optional[int] = None

class ToolAction(BaseModel):
    tool_name: str
    description: str
    data_summary: Optional[str] = None

class ChatResponse(BaseModel):
    session_id: str
    reply: str
    intent: str
    movies: List[MovieListItem] = []
    streaming_options: Dict[int, MovieStreamingAvailability] = {}
    suggested_followups: List[str] = []
    tools_invoked: List[ToolAction] = []

class ChatHistoryResponse(BaseModel):
    session_id: str
    total_messages: int
    messages: List[ChatMessage]
    active_movie_pool: List[str] = []

class ChatStartersResponse(BaseModel):
    starters: List[Dict[str, str]]
