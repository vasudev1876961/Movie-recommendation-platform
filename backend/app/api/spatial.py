# backend/app/api/spatial.py
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.app.database.database import get_db
from backend.app.services.spatial_biometrics import spatial_biometrics_service
from backend.app.schemas.spatial import (
    SpatialEnvironment,
    SpatialAudioPreset,
    BiometricResonanceReport,
    MeshNetworkStatus,
    BiometricSyncRequest
)

router = APIRouter(prefix="/api/spatial", tags=["CineSpatial & CinePulse Biometrics"])

@router.get("/environments", response_model=List[SpatialEnvironment])
def list_environments():
    """
    Returns available 3D Spatial Cinema Environments (IMAX Curved Horizon, Starlight Cosmic Nebula, Cyberpunk Holodeck, 1920s Art-Deco).
    """
    return spatial_biometrics_service.get_environments()

@router.get("/environments/{env_id}", response_model=SpatialEnvironment)
def get_environment_details(env_id: str):
    """
    Returns details, optical parameters, and screen curvature for a specific spatial environment.
    """
    env = spatial_biometrics_service.get_environment_by_id(env_id)
    if not env:
        raise HTTPException(status_code=404, detail=f"Environment '{env_id}' not found.")
    return env

@router.get("/audio-presets", response_model=List[SpatialAudioPreset])
def list_spatial_audio_presets():
    """
    Returns 3D binaural spatial audio presets with HRTF channels, room impulse decay, and Atmos virtual speaker configurations.
    """
    return spatial_biometrics_service.get_audio_presets()

@router.get("/mesh/status", response_model=MeshNetworkStatus)
def get_cinemesh_peer_status():
    """
    Returns decentralized edge-AI peer mesh status, active edge nodes, and local privacy metrics.
    """
    return spatial_biometrics_service.get_mesh_status()

@router.post("/biometrics/sync")
def sync_or_simulate_biometrics(payload: BiometricSyncRequest, db: Session = Depends(get_db)):
    """
    Ingests live biometric vitals or generates high-fidelity simulated autonomic telemetry (Heart Rate, HRV, GSR, VAD Affective Vector).
    """
    try:
        telemetry = spatial_biometrics_service.simulate_or_sync_biometrics(
            movie_id=payload.movie_id,
            timecode_sec=payload.current_timecode_sec,
            vitals=payload.vitals,
            stimulus=payload.simulate_stimulus,
            db=db
        )
        return telemetry
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to synchronize biometrics: {str(e)}")

@router.get("/biometrics/resonance/{movie_id}", response_model=BiometricResonanceReport)
def get_biometric_resonance_report(movie_id: int, db: Session = Depends(get_db)):
    """
    Computes viewer physiological synchronization score, autonomic coherence, and tension curve predictions for a movie.
    """
    try:
        report = spatial_biometrics_service.generate_resonance_report(movie_id=movie_id, db=db)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compute resonance report: {str(e)}")
