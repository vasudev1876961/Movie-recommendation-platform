# backend/app/services/agents/base_agent.py
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from backend.app.schemas.agents import AgentMessage

class BaseAgent(ABC):
    def __init__(
        self,
        agent_id: str,
        name: str,
        role: str,
        avatar: str,
        accent_color: str,
        description: str
    ):
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.avatar = avatar
        self.accent_color = accent_color
        self.description = description
        self.execution_times: List[float] = []

    def create_message(
        self,
        round_index: int,
        message_type: str,
        content: str,
        confidence: float = 0.95
    ) -> AgentMessage:
        return AgentMessage(
            agent_id=self.agent_id,
            agent_name=self.name,
            agent_role=self.role,
            agent_avatar=self.avatar,
            round_index=round_index,
            message_type=message_type,
            content=content,
            confidence=round(confidence, 3),
            timestamp=round(time.time(), 3)
        )

    def get_descriptor(self) -> Dict[str, Any]:
        return {
            "id": self.agent_id,
            "name": self.name,
            "role": self.role,
            "avatar": self.avatar,
            "accent_color": self.accent_color,
            "description": self.description,
        }
