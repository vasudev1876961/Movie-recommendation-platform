# backend/app/api/agents.py
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.app.database.database import get_db
from backend.app.schemas.agents import (
    AgentDeliberationRequest,
    AgentDeliberationResponse,
    QuickDebateRequest,
    QuickDebateResponse
)
from backend.app.services.agents.agent_orchestrator import agent_orchestrator

router = APIRouter(prefix="/api/agents", tags=["Multi-Agent Recommendation & Debate Network"])

@router.get("/roster")
def get_agent_roster():
    """Returns the active roster of specialized AI agents with roles and avatars."""
    return {
        "agents": agent_orchestrator.get_roster(),
        "total_agents": len(agent_orchestrator.get_roster())
    }

@router.get("/personas")
def get_personas():
    """Returns supported persona archetypes and their taste configuration profiles."""
    return {
        "personas": agent_orchestrator.get_personas()
    }

@router.post("/deliberate", response_model=AgentDeliberationResponse)
def run_agent_deliberation(
    request: AgentDeliberationRequest,
    db: Session = Depends(get_db)
):
    """Executes the full 5-agent deliberation and consensus recommendation pipeline."""
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="A query or prompt is required for agent deliberation.")

    archetype = request.archetype or "The Adaptive Cinephile"
    debate_rigor = request.debate_rigor or "Balanced & Analytical"
    limit = max(1, min(request.limit or 5, 20))

    response = agent_orchestrator.deliberate(
        query=query,
        db=db,
        archetype=archetype,
        debate_rigor=debate_rigor,
        limit=limit,
        user_id=request.user_id
    )

    return response

@router.post("/quick-debate", response_model=QuickDebateResponse)
def run_quick_debate(
    request: QuickDebateRequest,
    db: Session = Depends(get_db)
):
    """Conducts a rapid 2-round Scout vs Critic debate showdown on a specific movie."""
    if not request.movie_id and not request.movie_title:
        raise HTTPException(status_code=400, detail="Provide either movie_id or movie_title for quick debate.")

    debate_result = agent_orchestrator.quick_debate(
        db=db,
        movie_id=request.movie_id,
        movie_title=request.movie_title,
        user_context=request.user_context,
        debate_rigor=request.debate_rigor or "Balanced & Analytical"
    )

    if not debate_result:
        raise HTTPException(status_code=404, detail="Movie not found for debate showdown.")

    return debate_result

@router.get("/stats")
def get_agent_network_stats():
    """Returns telemetry and capabilities for the Multi-Agent Network."""
    return {
        "status": "online",
        "phase": 6,
        "engine": "Autonomous Multi-Agent Consensus Network",
        "agents_count": 5,
        "supported_personas": list(agent_orchestrator.get_personas().keys()),
        "debate_modes": ["Gentle & Agreeable", "Balanced & Analytical", "Fierce & Ruthless"]
    }
