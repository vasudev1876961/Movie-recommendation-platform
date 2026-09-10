# backend/app/services/chat/chat_session.py
import uuid
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from backend.app.schemas.chat import ChatMessage
from backend.app.schemas.movie import MovieListItem
from backend.app.schemas.streaming import MovieStreamingAvailability

class ChatSession:
    """Represents a stateful multi-turn conversational session with CineCopilot."""
    def __init__(self, session_id: str):
        self.session_id: str = session_id
        self.history: List[ChatMessage] = []
        self.active_movie_pool: List[MovieListItem] = []
        self.user_preferences: Dict[str, Any] = {
            "liked_genres": set(),
            "disliked_genres": set(),
            "preferred_actors": set(),
            "preferred_directors": set(),
            "max_runtime": None,
            "preferred_providers": set()
        }
        self.created_at: float = time.time()
        self.last_activity: float = time.time()

    def add_message(
        self,
        role: str,
        content: str,
        movies: Optional[List[MovieListItem]] = None,
        streaming_options: Optional[Dict[int, MovieStreamingAvailability]] = None,
        followups: Optional[List[str]] = None
    ) -> ChatMessage:
        msg = ChatMessage(
            role=role,
            content=content,
            timestamp=datetime.utcnow().strftime("%H:%M"),
            movies=movies,
            streaming_options=streaming_options,
            suggested_followups=followups
        )
        self.history.append(msg)
        self.last_activity = time.time()

        if movies:
            self.active_movie_pool = movies

        return msg

    def get_referenced_movie(self, query: str) -> Optional[MovieListItem]:
        """
        Resolves coreference expressions like 'the first one', 'the second film',
        or direct title matches against the active candidate pool.
        """
        if not self.active_movie_pool:
            return None

        q_lower = query.lower()

        # Ordinal checks
        ordinal_map = {
            "first": 0, "1st": 0, "one": 0,
            "second": 1, "2nd": 1, "two": 1,
            "third": 2, "3rd": 2, "three": 2,
            "fourth": 3, "4th": 3, "four": 3,
            "fifth": 4, "5th": 4, "five": 4,
            "last": len(self.active_movie_pool) - 1
        }

        for ord_word, idx in ordinal_map.items():
            if ord_word in q_lower and idx < len(self.active_movie_pool):
                return self.active_movie_pool[idx]

        # Direct title substring check in active pool
        for movie in self.active_movie_pool:
            if movie.title.lower() in q_lower:
                return movie

        # Default fallback to top recommended item if referencing "it" or "the movie"
        if any(w in q_lower for w in [" it ", " that ", "this film", "this movie", "the movie"]):
            return self.active_movie_pool[0]

        return None

class ChatSessionManager:
    """Singleton session registry managing active conversation memories."""
    def __init__(self):
        self._sessions: Dict[str, ChatSession] = {}

    def get_or_create(self, session_id: Optional[str] = None) -> ChatSession:
        if not session_id or session_id not in self._sessions:
            new_id = session_id or str(uuid.uuid4())
            self._sessions[new_id] = ChatSession(new_id)
            return self._sessions[new_id]
        return self._sessions[session_id]

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        return self._sessions.get(session_id)

    def clear_session(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def clean_inactive(self, max_age_seconds: int = 7200):
        now = time.time()
        expired = [sid for sid, s in self._sessions.items() if now - s.last_activity > max_age_seconds]
        for sid in expired:
            del self._sessions[sid]

chat_session_manager = ChatSessionManager()
