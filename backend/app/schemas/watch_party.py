# backend/app/schemas/watch_party.py
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class WatchPartyCreateRequest(BaseModel):
    movie_id: int
    room_title: Optional[str] = None
    host_nickname: str = "Host Cinephile"
    is_public: bool = True
    host_only_control: bool = False

class WatchPartyJoinRequest(BaseModel):
    room_code: str
    nickname: str = "Fellow Viewer"

class PartyParticipant(BaseModel):
    client_id: str
    nickname: str
    avatar: str
    role: str = "viewer"  # "host" or "viewer"
    joined_at: float

class PartyQueueItem(BaseModel):
    queue_id: str
    movie_id: int
    title: str
    poster_path: Optional[str] = ""
    rating: float = 0.0
    year: Optional[str] = ""
    trailer_key: Optional[str] = ""
    queued_by: str
    votes: int = 1
    voted_clients: List[str] = Field(default_factory=list)

class QueueAddRequest(BaseModel):
    movie_id: int
    client_id: str
    nickname: str

class QueueVoteRequest(BaseModel):
    queue_id: str
    client_id: str
    vote_delta: int = 1  # 1 for upvote, -1 for downvote

class WatchPartyRoom(BaseModel):
    room_code: str
    room_title: str
    movie_id: int
    movie_title: str
    poster_path: Optional[str] = ""
    trailer_key: Optional[str] = ""
    host_id: str
    host_nickname: str
    is_public: bool = True
    host_only_control: bool = False
    is_playing: bool = False
    current_time: float = 0.0
    playback_rate: float = 1.0
    updated_at: float
    created_at: float
    participants_count: int = 1

class PartyChatMessage(BaseModel):
    id: str
    sender_id: str
    nickname: str
    role: str = "viewer"
    avatar: str
    text: str
    timestamp: float
    formatted_time: str
    is_ai: bool = False

class PartyReactionEvent(BaseModel):
    id: str
    sender_id: str
    nickname: str
    emoji: str
    timestamp: float

class PartyStateResponse(BaseModel):
    room: WatchPartyRoom
    participants: List[PartyParticipant]
    queue: List[PartyQueueItem]
    recent_chat: List[PartyChatMessage]

class SyncActionMessage(BaseModel):
    action: str  # 'SYNC_PLAY', 'SYNC_PAUSE', 'SYNC_SEEK', 'SEND_CHAT', 'SEND_REACTION', 'AI_TRIVIA', 'QUEUE_UPDATE'
    room_code: str
    client_id: str
    nickname: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: Optional[float] = None
