# backend/app/services/watch_party_service.py
import time
import random
import string
import asyncio
from typing import Dict, List, Optional, Any
from fastapi import WebSocket
from backend.app.schemas.watch_party import (
    WatchPartyRoom,
    PartyParticipant,
    PartyQueueItem,
    PartyChatMessage,
    PartyStateResponse
)

class WatchPartyManager:
    """
    Real-Time Collaborative Watch Party Engine (CineSync).
    Coordinates room lifecycles, synchronized video playback states,
    in-room collaborative voting queues, real-time chat, floating reactions,
    and AI CineBot scene trivia popups.
    """

    def __init__(self):
        # Room Code -> Room Data
        self.rooms: Dict[str, Dict[str, Any]] = {}
        # Room Code -> List of active WebSockets
        self.active_sockets: Dict[str, Dict[str, WebSocket]] = {}
        # Initialize some active public demo watch parties for instant immersion
        self._seed_demo_parties()

    def _generate_room_code(self) -> str:
        chars = string.ascii_uppercase + "23456789"
        code = "CINE-" + "".join(random.choices(chars, k=4))
        while code in self.rooms:
            code = "CINE-" + "".join(random.choices(chars, k=4))
        return code

    def _seed_demo_parties(self):
        """Creates an active public party room so users arriving at the platform immediately have live rooms to explore."""
        code = "CINE-NOLAN"
        now = time.time()
        self.rooms[code] = {
            "room_code": code,
            "room_title": "Christopher Nolan 70mm Retrospective",
            "movie_id": 1,
            "movie_title": "Inception",
            "poster_path": "/9gk7adHYeDvHkCSEqAvQNLV5Uge.jpg",
            "trailer_key": "YoHD9XEInc0",
            "host_id": "host_solon",
            "host_nickname": "Aura_Curator",
            "is_public": True,
            "host_only_control": False,
            "is_playing": True,
            "current_time": 42.5,
            "playback_rate": 1.0,
            "created_at": now - 3600,
            "updated_at": now,
            "participants": {
                "host_solon": PartyParticipant(
                    client_id="host_solon",
                    nickname="Aura_Curator",
                    avatar="https://api.dicebear.com/7.x/bottts/svg?seed=Aura",
                    role="host",
                    joined_at=now - 3600
                ),
                "guest_1": PartyParticipant(
                    client_id="guest_1",
                    nickname="SciFiArchitect",
                    avatar="https://api.dicebear.com/7.x/bottts/svg?seed=SciFi",
                    role="viewer",
                    joined_at=now - 1200
                ),
                "guest_2": PartyParticipant(
                    client_id="guest_2",
                    nickname="NeoCinephile",
                    avatar="https://api.dicebear.com/7.x/bottts/svg?seed=Neo",
                    role="viewer",
                    joined_at=now - 600
                )
            },
            "queue": [
                PartyQueueItem(
                    queue_id="q_dark_knight",
                    movie_id=2,
                    title="The Dark Knight",
                    poster_path="/qJ2tW6WMUDux911r6m7haRef0WH.jpg",
                    rating=9.0,
                    year="2008",
                    trailer_key="EXeTwQWrcwY",
                    queued_by="SciFiArchitect",
                    votes=3,
                    voted_clients=["host_solon", "guest_1", "guest_2"]
                ),
                PartyQueueItem(
                    queue_id="q_interstellar",
                    movie_id=3,
                    title="Interstellar",
                    poster_path="/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg",
                    rating=8.7,
                    year="2014",
                    trailer_key="zSWdZVtXT7E",
                    queued_by="NeoCinephile",
                    votes=2,
                    voted_clients=["guest_1", "guest_2"]
                )
            ],
            "chat": [
                PartyChatMessage(
                    id="m_welcome",
                    sender_id="system",
                    nickname="CineSync System",
                    role="host",
                    avatar="https://api.dicebear.com/7.x/bottts/svg?seed=System",
                    text="Welcome to the Nolan 70mm Watch Party! The trailer is currently synchronized across all viewers.",
                    timestamp=now - 1500,
                    formatted_time="12:00",
                    is_ai=False
                ),
                PartyChatMessage(
                    id="m_trivia_1",
                    sender_id="cinebot",
                    nickname="CineBot AI",
                    role="viewer",
                    avatar="https://api.dicebear.com/7.x/bottts/svg?seed=CineBot",
                    text="🎬 CineBot Trivia: The iconic revolving hallway fight scene was shot entirely practically inside a massive 100-foot rotating centrifuge drum with zero digital green screen.",
                    timestamp=now - 800,
                    formatted_time="12:12",
                    is_ai=True
                )
            ]
        }
        self.active_sockets[code] = {}

    def create_room(
        self,
        movie_id: int,
        movie_title: str,
        poster_path: str,
        trailer_key: str,
        host_nickname: str = "Host Cinephile",
        room_title: Optional[str] = None,
        is_public: bool = True,
        host_only_control: bool = False
    ) -> WatchPartyRoom:
        code = self._generate_room_code()
        now = time.time()
        host_id = f"host_{int(now * 1000)}"

        if not room_title:
            room_title = f"{movie_title} — Watch Party"

        room_data = {
            "room_code": code,
            "room_title": room_title,
            "movie_id": movie_id,
            "movie_title": movie_title,
            "poster_path": poster_path,
            "trailer_key": trailer_key,
            "host_id": host_id,
            "host_nickname": host_nickname,
            "is_public": is_public,
            "host_only_control": host_only_control,
            "is_playing": False,
            "current_time": 0.0,
            "playback_rate": 1.0,
            "created_at": now,
            "updated_at": now,
            "participants": {
                host_id: PartyParticipant(
                    client_id=host_id,
                    nickname=host_nickname,
                    avatar=f"https://api.dicebear.com/7.x/bottts/svg?seed={host_nickname}",
                    role="host",
                    joined_at=now
                )
            },
            "queue": [],
            "chat": [
                PartyChatMessage(
                    id=f"msg_{int(now*1000)}",
                    sender_id="system",
                    nickname="CineSync System",
                    role="host",
                    avatar="https://api.dicebear.com/7.x/bottts/svg?seed=System",
                    text=f"Watch Party created by {host_nickname}! Share room code {code} to invite friends.",
                    timestamp=now,
                    formatted_time=time.strftime("%H:%M", time.localtime(now)),
                    is_ai=False
                )
            ]
        }

        self.rooms[code] = room_data
        self.active_sockets[code] = {}

        return self._build_room_schema(room_data)

    def _build_room_schema(self, r: Dict[str, Any]) -> WatchPartyRoom:
        return WatchPartyRoom(
            room_code=r["room_code"],
            room_title=r["room_title"],
            movie_id=r["movie_id"],
            movie_title=r["movie_title"],
            poster_path=r.get("poster_path", ""),
            trailer_key=r.get("trailer_key", ""),
            host_id=r["host_id"],
            host_nickname=r["host_nickname"],
            is_public=r["is_public"],
            host_only_control=r["host_only_control"],
            is_playing=r["is_playing"],
            current_time=r["current_time"],
            playback_rate=r["playback_rate"],
            updated_at=r["updated_at"],
            created_at=r["created_at"],
            participants_count=len(r["participants"])
        )

    def get_room(self, room_code: str) -> Optional[PartyStateResponse]:
        if room_code not in self.rooms:
            return None
        r = self.rooms[room_code]
        return PartyStateResponse(
            room=self._build_room_schema(r),
            participants=list(r["participants"].values()),
            queue=sorted(r["queue"], key=lambda q: q.votes, reverse=True),
            recent_chat=r["chat"][-50:]
        )

    def list_public_rooms(self) -> List[WatchPartyRoom]:
        result = []
        for r in self.rooms.values():
            if r["is_public"]:
                result.append(self._build_room_schema(r))
        return sorted(result, key=lambda x: x.participants_count, reverse=True)

    def join_participant(self, room_code: str, client_id: str, nickname: str) -> Optional[PartyParticipant]:
        if room_code not in self.rooms:
            return None
        r = self.rooms[room_code]
        now = time.time()
        role = "host" if client_id == r["host_id"] else "viewer"
        avatar = f"https://api.dicebear.com/7.x/bottts/svg?seed={nickname}"

        p = PartyParticipant(
            client_id=client_id,
            nickname=nickname,
            avatar=avatar,
            role=role,
            joined_at=now
        )
        r["participants"][client_id] = p
        return p

    def remove_participant(self, room_code: str, client_id: str):
        if room_code in self.rooms and client_id in self.rooms[room_code]["participants"]:
            # If the leaving participant is not the original host, remove them
            p = self.rooms[room_code]["participants"].pop(client_id, None)
            return p
        return None

    def sync_playback(
        self,
        room_code: str,
        client_id: str,
        action: str, # 'SYNC_PLAY', 'SYNC_PAUSE', 'SYNC_SEEK'
        timestamp: float
    ) -> Optional[Dict[str, Any]]:
        if room_code not in self.rooms:
            return None
        r = self.rooms[room_code]

        # Check host control lock
        if r["host_only_control"] and client_id != r["host_id"]:
            return None # Locked to host

        now = time.time()
        r["current_time"] = max(0.0, timestamp)
        r["updated_at"] = now

        if action == "SYNC_PLAY":
            r["is_playing"] = True
        elif action == "SYNC_PAUSE":
            r["is_playing"] = False

        return {
            "is_playing": r["is_playing"],
            "current_time": r["current_time"],
            "updated_at": r["updated_at"]
        }

    def add_chat_message(
        self,
        room_code: str,
        sender_id: str,
        nickname: str,
        text: str,
        is_ai: bool = False
    ) -> Optional[PartyChatMessage]:
        if room_code not in self.rooms:
            return None
        r = self.rooms[room_code]
        now = time.time()
        role = "host" if sender_id == r["host_id"] else "viewer"
        avatar = f"https://api.dicebear.com/7.x/bottts/svg?seed={'CineBot' if is_ai else nickname}"

        msg = PartyChatMessage(
            id=f"msg_{int(now*1000)}_{random.randint(100, 999)}",
            sender_id=sender_id,
            nickname=nickname,
            role=role,
            avatar=avatar,
            text=text,
            timestamp=now,
            formatted_time=time.strftime("%H:%M", time.localtime(now)),
            is_ai=is_ai
        )
        r["chat"].append(msg)
        if len(r["chat"]) > 100:
            r["chat"] = r["chat"][-100:]
        return msg

    def add_to_queue(
        self,
        room_code: str,
        movie_id: int,
        title: str,
        poster_path: str,
        rating: float,
        year: str,
        trailer_key: str,
        queued_by: str,
        client_id: str
    ) -> Optional[PartyQueueItem]:
        if room_code not in self.rooms:
            return None
        r = self.rooms[room_code]

        # Check if already in queue
        for item in r["queue"]:
            if item.movie_id == movie_id:
                # Upvote existing
                if client_id not in item.voted_clients:
                    item.votes += 1
                    item.voted_clients.append(client_id)
                return item

        queue_id = f"q_{movie_id}_{int(time.time())}"
        new_item = PartyQueueItem(
            queue_id=queue_id,
            movie_id=movie_id,
            title=title,
            poster_path=poster_path,
            rating=rating,
            year=year,
            trailer_key=trailer_key,
            queued_by=queued_by,
            votes=1,
            voted_clients=[client_id]
        )
        r["queue"].append(new_item)
        return new_item

    def vote_queue_item(
        self,
        room_code: str,
        queue_id: str,
        client_id: str,
        vote_delta: int = 1
    ) -> Optional[List[PartyQueueItem]]:
        if room_code not in self.rooms:
            return None
        r = self.rooms[room_code]

        for item in r["queue"]:
            if item.queue_id == queue_id:
                if vote_delta > 0:
                    if client_id not in item.voted_clients:
                        item.votes += 1
                        item.voted_clients.append(client_id)
                else:
                    if client_id in item.voted_clients:
                        item.votes = max(0, item.votes - 1)
                        item.voted_clients.remove(client_id)
                break

        r["queue"] = sorted(r["queue"], key=lambda q: q.votes, reverse=True)
        return r["queue"]

    def advance_queue(self, room_code: str) -> Optional[Dict[str, Any]]:
        """Pops the top queued movie and loads it as the active room movie."""
        if room_code not in self.rooms or not self.rooms[room_code]["queue"]:
            return None
        r = self.rooms[room_code]
        r["queue"] = sorted(r["queue"], key=lambda q: q.votes, reverse=True)
        next_movie = r["queue"].pop(0)

        r["movie_id"] = next_movie.movie_id
        r["movie_title"] = next_movie.title
        r["poster_path"] = next_movie.poster_path
        r["trailer_key"] = next_movie.trailer_key
        r["current_time"] = 0.0
        r["is_playing"] = True
        r["updated_at"] = time.time()

        return {
            "movie_id": r["movie_id"],
            "movie_title": r["movie_title"],
            "poster_path": r["poster_path"],
            "trailer_key": r["trailer_key"],
            "current_time": 0.0,
            "is_playing": True
        }

    def generate_ai_trivia(self, room_code: str, movie_title: str, current_time: float) -> PartyChatMessage:
        """Generates contextual AI CineBot trivia for the current trailer moment."""
        time_str = time.strftime("%M:%S", time.gmtime(current_time))
        trivia_library = [
            f"🎬 CineBot Trivia ({time_str}): Sound designers captured organic low-frequency seismic hums to subconsciously heighten anxiety during this sequence.",
            f"🎬 CineBot Trivia ({time_str}): The director insisted on continuous long takes here, with cast members rehearsing camera choreography for 3 weeks prior.",
            f"🎬 CineBot Trivia ({time_str}): The musical score here drops the master orchestra to a solo cello, creating an intimate contrast before the third act crescendo.",
            f"🎬 CineBot Trivia ({time_str}): Notice the color temperature shift: the palette cools by 1200 Kelvin to visually signal the characters' psychological descent."
        ]
        chosen = random.choice(trivia_library)
        return self.add_chat_message(
            room_code=room_code,
            sender_id="cinebot",
            nickname="CineBot AI",
            text=chosen,
            is_ai=True
        )

    # WebSocket Management
    def register_socket(self, room_code: str, client_id: str, ws: WebSocket):
        if room_code not in self.active_sockets:
            self.active_sockets[room_code] = {}
        self.active_sockets[room_code][client_id] = ws

    def unregister_socket(self, room_code: str, client_id: str):
        if room_code in self.active_sockets:
            self.active_sockets[room_code].pop(client_id, None)

    async def broadcast_to_room(
        self,
        room_code: str,
        message: Dict[str, Any],
        exclude_client_id: Optional[str] = None
    ):
        if room_code not in self.active_sockets:
            return
        dead_clients = []
        for cid, ws in list(self.active_sockets[room_code].items()):
            if exclude_client_id and cid == exclude_client_id:
                continue
            try:
                await ws.send_json(message)
            except Exception:
                dead_clients.append(cid)

        for dead in dead_clients:
            self.unregister_socket(room_code, dead)

# Global singleton manager
watch_party_manager = WatchPartyManager()
