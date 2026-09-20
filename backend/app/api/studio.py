# backend/app/api/studio.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.app.database.database import get_db
from backend.app.services.neuro_studio import neuro_studio
from backend.app.schemas.studio import (
    DubbingVoice,
    DubbingRequest,
    DubbingManifest,
    ReCutVibe,
    ReCutRequest,
    ReCutTreatment,
    ExportDossierRequest
)

router = APIRouter(prefix="/api/studio", tags=["Neuro-Cinematic Studio"])

@router.get("/voices", response_model=List[DubbingVoice])
def get_dubbing_voices(language: str = Query(None, description="Optional language filter: en, es, fr, ja, de, hi")):
    """
    Returns available LinguaCine neural voice personas and multilingual acoustic profiles.
    """
    voices = neuro_studio.get_available_voices()
    if language:
        voices = [v for v in voices if v.language_code == language.lower()]
    return voices

@router.get("/vibes", response_model=List[ReCutVibe])
def get_preset_vibes():
    """
    Returns curated directorial re-cut vibes with live CSS LUT color filters, soundtrack keys, and editing styles.
    """
    return neuro_studio.get_preset_vibes()

@router.post("/recut", response_model=ReCutTreatment)
def generate_recut_treatment(payload: ReCutRequest, db: Session = Depends(get_db)):
    """
    Synthesizes an alternate-genre AI Director's Cut treatment, shot list, acoustic blueprint, and live LUT filter.
    """
    try:
        treatment = neuro_studio.generate_trailer_recut(
            movie_id=payload.movie_id,
            vibe_id=payload.vibe_id,
            custom_prompt=payload.custom_prompt,
            intensity=payload.intensity,
            db=db
        )
        return treatment
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate Director's Cut: {str(e)}")

@router.post("/dub", response_model=DubbingManifest)
def generate_multilingual_dub(payload: DubbingRequest, db: Session = Depends(get_db)):
    """
    Generates localized multilingual voiceover script, word timing markers for real-time karaoke sync, and voice parameters.
    """
    try:
        manifest = neuro_studio.generate_multilingual_dub(
            movie_id=payload.movie_id,
            language=payload.language,
            voice_id=payload.voice_id,
            script_style=payload.script_style,
            custom_monologue=payload.custom_monologue,
            db=db
        )
        return manifest
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate multilingual dubbing manifest: {str(e)}")

@router.post("/export")
def export_directors_cut_dossier(payload: ExportDossierRequest):
    """
    Compiles an exportable Markdown or JSON Director's Cut treatment dossier.
    """
    if payload.format.lower() == "json":
        return {
            "treatment": payload.treatment.model_dump(),
            "dubbing": payload.dubbing.model_dump() if payload.dubbing else None
        }
    
    markdown_content = neuro_studio.export_treatment_markdown(payload.treatment, payload.dubbing)
    safe_title = payload.treatment.movie_title.lower().replace(" ", "_")
    return {
        "format": "markdown",
        "filename": f"directors_cut_{safe_title}_{payload.treatment.vibe.vibe_id}.md",
        "content": markdown_content
    }
