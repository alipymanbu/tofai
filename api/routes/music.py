from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
from uuid import uuid4
from datetime import datetime

from models.job import Job, JobStatus, JobType
from services.ai.tts_service import TTSService
from services.ai.script_audio_service import ScriptAudioService
from utils.audio_storage import LocalAudioStorage
from services.storage.database import get_db

router = APIRouter()

# Initialize services
tts_service = TTSService()
audio_storage = LocalAudioStorage()
script_audio_service = ScriptAudioService()

class TTSRequest(BaseModel):
    """Model for TTS generation request."""
    text: str
    voice_id: str = "21m00Tcm4TlvDq8ikWAM"  # Default ElevenLabs voice
    model: str = "eleven_monolingual_v1"
    
class VoiceListResponse(BaseModel):
    """Model for voice list response."""
    voices: List[Dict[str, Any]]

class AudioResponse(BaseModel):
    """Model for audio generation response."""
    url_path: str
    duration: float
    filename: str

class ScriptAudioRequest(BaseModel):
    """Model for script audio generation request."""
    voice_id: str = "21m00Tcm4TlvDq8ikWAM"
    optimize_narration: bool = True

class ScriptAudioResponse(BaseModel):
    """Model for script audio generation response."""
    success: bool
    scenes: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]
    total_scenes: int
    completed_scenes: int
    failed_scenes: int

@router.post("/sessions/{session_id}/audio/tts", response_model=AudioResponse)
async def generate_tts(
    session_id: str,
    request: TTSRequest,
    background_tasks: BackgroundTasks,
    db = Depends(get_db)
):
    """Generate TTS audio from text."""
    # Generate speech
    result = await tts_service.generate_speech(
        text=request.text,
        voice_id=request.voice_id,
        model=request.model
    )
    
    if not result.success:
        raise HTTPException(
            status_code=500,
            detail=f"TTS generation failed: {result.error}"
        )
    
    # Save audio data
    storage_result = await audio_storage.save_audio(
        audio_data=result.audio_data,
        session_id=session_id,
        filename=f"tts_{uuid4()}.mp3"
    )
    
    if not storage_result["success"]:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save audio: {storage_result['error']}"
        )
    
    # Return the response
    return AudioResponse(
        url_path=storage_result["url_path"],
        duration=result.duration,
        filename=storage_result["filename"]
    )

@router.get("/sessions/{session_id}/audio/voices", response_model=VoiceListResponse)
async def get_available_voices(session_id: str):
    """Get list of available TTS voices."""
    result = await tts_service.get_available_voices()
    
    if not result["success"]:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch voices: {result['error']}"
        )
    
    return VoiceListResponse(voices=result["voices"])

@router.get("/media/{session_id}/{filename}")
async def get_audio_file(session_id: str, filename: str):
    """Serve audio file."""
    file_path = await audio_storage.get_audio_path(session_id, filename)
    
    if not file_path:
        raise HTTPException(
            status_code=404,
            detail="Audio file not found"
        )
    
    return FileResponse(file_path, media_type="audio/mpeg")

@router.post(
    "/sessions/{session_id}/script/audio",
    response_model=ScriptAudioResponse
)
async def generate_script_audio(
    session_id: str,
    request: ScriptAudioRequest,
    db = Depends(get_db)
):
    """Generate audio for all scenes in a script."""
    # Get the script from the database
    session = await db.sessions.find_one({"id": session_id})
    
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )
    
    script = session.get("script")
    
    if not script:
        raise HTTPException(
            status_code=404,
            detail="Script not found for this session"
        )
    
    # Generate audio for the script
    result = await script_audio_service.generate_script_audio(
        session_id=session_id,
        script=script,
        voice_id=request.voice_id
    )
    
    return result