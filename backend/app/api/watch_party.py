# backend/app/api/watch_party.py
import time
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session
from backend.app.database.database import get_db
from backend.app.models.movie import Movie
from backend.app.schemas.watch_party import (
    WatchPartyCreateRequest,
    WatchPartyJoinRequest,
    WatchPartyRoom,
    PartyStateResponse,
    PartyParticipant,
    PartyQueueItem,
    QueueAddRequest,
    QueueVoteRequest,
    PartyChatMessage
)
from backend.app.services.watch_party_service import watch_party_manager

router = APIRouter(prefix="/api/watch-party", tags=["Real-Time Collaborative Watch Parties"])

@router.post("/create", response_model=WatchPartyRoom)
def create_watch_party_room(payload: WatchPartyCreateRequest, db: Session = Depends(get_db)):
    """
    Creates a new real-time watch party theater with custom sync lock and host controls.
    """
    movie = db.query(Movie).filter(Movie.id == payload.movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail=f"Movie {payload.movie_id} not found.")

    room = watch_party_manager.create_room(
        movie_id=movie.id,
        movie_title=movie.title,
        poster_path=movie.poster_path or "",
        trailer_key=movie.trailer or "YoHD9XEInc0",
        host_nickname=payload.host_nickname,
        room_title=payload.room_title,
        is_public=payload.is_public,
        host_only_control=payload.host_only_control
    )
    return room

@router.get("/rooms", response_model=List[WatchPartyRoom])
def list_active_public_rooms():
    """
    Lists all active public watch party rooms currently streaming.
    """
    return watch_party_manager.list_public_rooms()

@router.get("/{room_code}", response_model=PartyStateResponse)
def get_watch_party_details(room_code: str):
    """
    Retrieves full room state, connected participants, up-next queue, and recent chat history.
    """
    state = watch_party_manager.get_room(room_code.upper())
    if not state:
        raise HTTPException(status_code=404, detail=f"Watch party room {room_code} not found.")
    return state

@router.post("/{room_code}/join", response_model=PartyParticipant)
def join_watch_party(room_code: str, payload: WatchPartyJoinRequest):
    """
    Registers participant presence in the room.
    """
    p = watch_party_manager.join_participant(
        room_code=room_code.upper(),
        client_id=f"client_{int(time.time()*1000)}",
        nickname=payload.nickname
    )
    if not p:
        raise HTTPException(status_code=404, detail=f"Watch party room {room_code} not found.")
    return p

@router.post("/{room_code}/queue", response_model=PartyQueueItem)
def add_movie_to_party_queue(
    room_code: str,
    payload: QueueAddRequest,
    db: Session = Depends(get_db)
):
    """
    Adds a catalog movie to the collaborative Up-Next playlist queue.
    """
    movie = db.query(Movie).filter(Movie.id == payload.movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail=f"Movie {payload.movie_id} not found.")

    item = watch_party_manager.add_to_queue(
        room_code=room_code.upper(),
        movie_id=movie.id,
        title=movie.title,
        poster_path=movie.poster_path or "",
        rating=movie.rating or 0.0,
        year=movie.release_date.split("-")[0] if movie.release_date else "",
        trailer_key=movie.trailer or "YoHD9XEInc0",
        queued_by=payload.nickname,
        client_id=payload.client_id
    )
    if not item:
        raise HTTPException(status_code=404, detail=f"Watch party room {room_code} not found.")
    return item

@router.post("/{room_code}/queue/vote", response_model=List[PartyQueueItem])
def vote_on_queue_item(room_code: str, payload: QueueVoteRequest):
    """
    Casts an upvote or downvote on a queued movie to influence play order.
    """
    updated_queue = watch_party_manager.vote_queue_item(
        room_code=room_code.upper(),
        queue_id=payload.queue_id,
        client_id=payload.client_id,
        vote_delta=payload.vote_delta
    )
    if updated_queue is None:
        raise HTTPException(status_code=404, detail=f"Watch party room {room_code} or item not found.")
    return updated_queue

@router.post("/{room_code}/advance")
def advance_to_next_in_queue(room_code: str):
    """
    Advances to the highest-voted movie in the room queue.
    """
    res = watch_party_manager.advance_queue(room_code.upper())
    if not res:
        raise HTTPException(status_code=400, detail="No movies in queue to advance.")
    return res

@router.post("/{room_code}/trivia", response_model=PartyChatMessage)
def trigger_cinebot_trivia(room_code: str, current_time: float = Query(default=0.0)):
    """
    Requests AI CineBot to generate behind-the-scenes trivia for the current trailer moment.
    """
    state = watch_party_manager.get_room(room_code.upper())
    if not state:
        raise HTTPException(status_code=404, detail=f"Watch party room {room_code} not found.")

    msg = watch_party_manager.generate_ai_trivia(
        room_code=room_code.upper(),
        movie_title=state.room.movie_title,
        current_time=current_time
    )
    return msg

@router.websocket("/ws/{room_code}")
async def watch_party_websocket(
    websocket: WebSocket,
    room_code: str,
    client_id: Optional[str] = Query(default=None),
    nickname: Optional[str] = Query(default="Viewer")
):
    """
    Bidirectional WebSocket connection for synchronized playback,
    live chat, floating reaction emissions, and AI CineBot notifications.
    """
    room_code = room_code.upper()
    await websocket.accept()

    cid = client_id or f"ws_{int(time.time()*1000)}"
    watch_party_manager.register_socket(room_code, cid, websocket)
    watch_party_manager.join_participant(room_code, cid, nickname)

    # Broadcast user joined event
    await watch_party_manager.broadcast_to_room(
        room_code,
        {
            "action": "USER_JOINED",
            "client_id": cid,
            "nickname": nickname,
            "timestamp": time.time()
        }
    )

    try:
        while True:
            raw_text = await websocket.receive_text()
            data = json.loads(raw_text)
            action = data.get("action")

            if action in ["SYNC_PLAY", "SYNC_PAUSE", "SYNC_SEEK"]:
                ts = float(data.get("payload", {}).get("timestamp", 0.0))
                sync_res = watch_party_manager.sync_playback(room_code, cid, action, ts)
                if sync_res:
                    await watch_party_manager.broadcast_to_room(
                        room_code,
                        {
                            "action": action,
                            "client_id": cid,
                            "nickname": nickname,
                            "payload": sync_res,
                            "timestamp": time.time()
                        },
                        exclude_client_id=cid
                    )

            elif action == "SEND_CHAT":
                text = data.get("payload", {}).get("text", "").strip()
                if text:
                    msg = watch_party_manager.add_chat_message(
                        room_code=room_code,
                        sender_id=cid,
                        nickname=nickname,
                        text=text
                    )
                    if msg:
                        await watch_party_manager.broadcast_to_room(
                            room_code,
                            {
                                "action": "RECEIVE_CHAT",
                                "message": msg.model_dump()
                            }
                        )

            elif action == "SEND_REACTION":
                emoji = data.get("payload", {}).get("emoji", "🍿")
                await watch_party_manager.broadcast_to_room(
                    room_code,
                    {
                        "action": "RECEIVE_REACTION",
                        "sender_id": cid,
                        "nickname": nickname,
                        "emoji": emoji,
                        "timestamp": time.time()
                    }
                )

            elif action == "REQUEST_TRIVIA":
                ts = float(data.get("payload", {}).get("timestamp", 0.0))
                title = data.get("payload", {}).get("movie_title", "Movie")
                t_msg = watch_party_manager.generate_ai_trivia(room_code, title, ts)
                await watch_party_manager.broadcast_to_room(
                    room_code,
                    {
                        "action": "RECEIVE_CHAT",
                        "message": t_msg.model_dump()
                    }
                )

            elif action == "ADVANCE_QUEUE":
                adv = watch_party_manager.advance_queue(room_code)
                if adv:
                    await watch_party_manager.broadcast_to_room(
                        room_code,
                        {
                            "action": "MOVIE_CHANGED",
                            "payload": adv
                        }
                    )

    except WebSocketDisconnect:
        watch_party_manager.unregister_socket(room_code, cid)
        watch_party_manager.remove_participant(room_code, cid)
        await watch_party_manager.broadcast_to_room(
            room_code,
            {
                "action": "USER_LEFT",
                "client_id": cid,
                "nickname": nickname,
                "timestamp": time.time()
            }
        )
    except Exception:
        watch_party_manager.unregister_socket(room_code, cid)
