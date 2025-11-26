"""
Rohimaya Audiobook Engine - FastAPI Application
Production HTTP API for audiobook generation
"""

import os
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, status, Depends, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from .database import db
from .auth import get_current_user
from .worker import enqueue_job, worker_loop, get_queue_status

# Load environment variables from env/.env
env_path = Path(__file__).parent.parent.parent.parent / "env" / ".env"
load_dotenv(dotenv_path=env_path)

# Initialize FastAPI app
app = FastAPI(
    title="Rohimaya Audiobook Engine API",
    description="Production API for generating studio-quality audiobooks from manuscripts",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# PYDANTIC MODELS (Request/Response Schemas)
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str
    timestamp: str


class JobCreateRequest(BaseModel):
    """Create new audiobook job"""
    title: str = Field(..., min_length=1, max_length=200)
    author: Optional[str] = Field(None, max_length=200)
    source_type: str = Field(..., description="upload, paste, google_drive, or url")
    source_path: Optional[str] = Field(None, description="Storage path if uploaded, null if pasted")
    manuscript_text: Optional[str] = Field(None, description="Text content if pasted")
    mode: str = Field(..., description="single_voice or dual_voice")
    tts_provider: str = Field(..., description="openai, elevenlabs, or inworld")
    narrator_voice_id: str = Field(..., description="Voice ID for narrator")
    character_voice_id: Optional[str] = Field(None, description="Voice ID for character (dual-voice only)")
    character_name: Optional[str] = Field(None, description="Character name (dual-voice only)")
    audio_format: str = Field(default="mp3", description="mp3, wav, flac, or m4b")
    audio_bitrate: str = Field(default="128k", description="128k, 192k, or 320k")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "My Audiobook",
                "author": "John Doe",
                "source_type": "upload",
                "source_path": "user123/manuscript.txt",
                "mode": "single_voice",
                "tts_provider": "openai",
                "narrator_voice_id": "alloy",
                "audio_format": "mp3",
                "audio_bitrate": "128k",
            }
        }


class JobResponse(BaseModel):
    """Job details response"""
    id: str
    user_id: str
    status: str
    mode: str
    title: str
    author: Optional[str]
    source_type: str
    source_path: Optional[str]
    tts_provider: str
    narrator_voice_id: str
    character_voice_id: Optional[str]
    character_name: Optional[str]
    audio_format: str
    audio_bitrate: str
    audio_path: Optional[str]
    duration_seconds: Optional[int]
    file_size_bytes: Optional[int]
    progress_percent: Optional[float]
    error_message: Optional[str]
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]


class VoiceInfo(BaseModel):
    """Voice metadata"""
    voice_id: str
    name: str
    provider: str
    gender: Optional[str]
    language: str
    description: Optional[str]


class QueueStatusResponse(BaseModel):
    """Worker queue status"""
    queued_jobs: int
    processing_jobs: int
    total: int


# ============================================================================
# API ROUTES
# ============================================================================

@app.get(
    "/",
    summary="API Root",
    tags=["System"],
)
async def root() -> Dict[str, Any]:
    """API root endpoint"""
    return {
        "service": "Rohimaya Audiobook Engine API",
        "version": "0.2.0",
        "status": "operational",
        "docs": "/docs",
        "health": "/health",
    }


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    tags=["System"],
)
async def health_check() -> HealthResponse:
    """Health check endpoint for monitoring"""
    return HealthResponse(
        status="ok",
        service="rohimaya-engine",
        version="0.2.0",
        timestamp=datetime.utcnow().isoformat() + "Z"
    )


# ============================================================================
# JOB MANAGEMENT ENDPOINTS
# ============================================================================

@app.post(
    "/jobs",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Audiobook Job",
    tags=["Jobs"],
)
async def create_job(
    request: JobCreateRequest,
    user_id: str = Depends(get_current_user)
) -> JobResponse:
    """
    Create a new audiobook generation job

    Requires authentication. The job will be queued for processing.
    """
    # Validate mode
    if request.mode not in ["single_voice", "dual_voice"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mode must be 'single_voice' or 'dual_voice'"
        )

    # Validate TTS provider
    if request.tts_provider not in ["openai", "elevenlabs", "inworld"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="TTS provider must be 'openai', 'elevenlabs', or 'inworld'"
        )

    # Validate dual-voice requirements
    if request.mode == "dual_voice":
        if not request.character_voice_id or not request.character_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dual-voice mode requires character_voice_id and character_name"
            )

    # Handle pasted text - upload to storage
    if request.source_type == "paste" and request.manuscript_text:
        # Upload text as file
        filename = f"{request.title.replace(' ', '_')}.txt"
        source_path = db.upload_manuscript(
            user_id=user_id,
            filename=filename,
            file_content=request.manuscript_text.encode("utf-8")
        )
    else:
        source_path = request.source_path

    # Create job in database
    job_data = {
        "user_id": user_id,
        "status": "pending",
        "mode": request.mode,
        "title": request.title,
        "author": request.author,
        "source_type": request.source_type,
        "source_path": source_path,
        "tts_provider": request.tts_provider,
        "narrator_voice_id": request.narrator_voice_id,
        "character_voice_id": request.character_voice_id,
        "character_name": request.character_name,
        "audio_format": request.audio_format,
        "audio_bitrate": request.audio_bitrate,
        "progress_percent": 0.0,
    }

    job = db.create_job(job_data)

    # Enqueue job for processing
    await enqueue_job(job["id"])

    return JobResponse(**job)


@app.get(
    "/jobs/{job_id}",
    response_model=JobResponse,
    summary="Get Job Status",
    tags=["Jobs"],
)
async def get_job(
    job_id: str,
    user_id: str = Depends(get_current_user)
) -> JobResponse:
    """
    Get job status and details

    Requires authentication. User can only access their own jobs.
    """
    job = db.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )

    # Verify ownership
    if job["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this job"
        )

    return JobResponse(**job)


@app.get(
    "/jobs",
    response_model=List[JobResponse],
    summary="List User Jobs",
    tags=["Jobs"],
)
async def list_jobs(
    user_id: str = Depends(get_current_user),
    status_filter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[JobResponse]:
    """
    List all jobs for the authenticated user

    Optional filters:
    - status: Filter by status (pending, processing, completed, failed)
    - limit: Number of jobs to return (default 50)
    - offset: Pagination offset (default 0)
    """
    jobs = db.get_user_jobs(
        user_id=user_id,
        status=status_filter,
        limit=limit,
        offset=offset
    )

    return [JobResponse(**job) for job in jobs]


@app.get(
    "/jobs/{job_id}/download",
    summary="Download Audiobook",
    tags=["Jobs"],
)
async def download_audiobook(
    job_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Get download URL for completed audiobook

    Returns a redirect to a signed Supabase Storage URL (expires in 1 hour)
    """
    job = db.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )

    # Verify ownership
    if job["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this job"
        )

    # Check if completed
    if job["status"] != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job is not completed (current status: {job['status']})"
        )

    # Get signed download URL
    download_url = db.get_download_url(job["audio_path"], expires_in=3600)

    # Redirect to download URL
    return RedirectResponse(url=download_url)


@app.delete(
    "/jobs/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Job",
    tags=["Jobs"],
)
async def delete_job(
    job_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Delete a job and its associated files

    Requires authentication. User can only delete their own jobs.
    """
    job = db.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )

    # Verify ownership
    if job["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this job"
        )

    # Delete storage files if they exist
    if job["source_path"]:
        db.delete_storage_file("manuscripts", job["source_path"])

    if job["audio_path"]:
        db.delete_storage_file("audiobooks", job["audio_path"])

    # Delete job from database (CASCADE deletes job_files)
    db.delete_job(job_id)

    return None


# ============================================================================
# VOICE MANAGEMENT ENDPOINTS
# ============================================================================

@app.get(
    "/voices",
    response_model=List[VoiceInfo],
    summary="List Available Voices",
    tags=["Voices"],
)
async def list_voices(provider: Optional[str] = None) -> List[VoiceInfo]:
    """
    List available TTS voices

    Optional filter by provider: openai, elevenlabs, inworld
    """
    voices = []

    # OpenAI voices
    if not provider or provider == "openai":
        openai_voices = [
            VoiceInfo(voice_id="alloy", name="Alloy", provider="openai", gender="neutral", language="en", description="Neutral and balanced"),
            VoiceInfo(voice_id="echo", name="Echo", provider="openai", gender="male", language="en", description="Deep and resonant"),
            VoiceInfo(voice_id="fable", name="Fable", provider="openai", gender="male", language="en", description="Warm and storytelling"),
            VoiceInfo(voice_id="onyx", name="Onyx", provider="openai", gender="male", language="en", description="Deep and authoritative"),
            VoiceInfo(voice_id="nova", name="Nova", provider="openai", gender="female", language="en", description="Bright and energetic"),
            VoiceInfo(voice_id="shimmer", name="Shimmer", provider="openai", gender="female", language="en", description="Soft and gentle"),
        ]
        voices.extend(openai_voices)

    # ElevenLabs voices (placeholder - would fetch from API in production)
    if not provider or provider == "elevenlabs":
        elevenlabs_voices = [
            VoiceInfo(voice_id="21m00Tcm4TlvDq8ikWAM", name="Rachel", provider="elevenlabs", gender="female", language="en", description="Calm and professional"),
            VoiceInfo(voice_id="AZnzlk1XvdvUeBnXmlld", name="Domi", provider="elevenlabs", gender="female", language="en", description="Strong and confident"),
            VoiceInfo(voice_id="EXAVITQu4vr4xnSDxMaL", name="Bella", provider="elevenlabs", gender="female", language="en", description="Soft and young"),
            VoiceInfo(voice_id="ErXwobaYiN019PkySvjV", name="Antoni", provider="elevenlabs", gender="male", language="en", description="Well-rounded and versatile"),
            VoiceInfo(voice_id="MF3mGyEYCl7XYWbV9V6O", name="Elli", provider="elevenlabs", gender="female", language="en", description="Emotional and expressive"),
            VoiceInfo(voice_id="TxGEqnHWrfWFTfGW9XjX", name="Josh", provider="elevenlabs", gender="male", language="en", description="Deep and narration-focused"),
        ]
        voices.extend(elevenlabs_voices)

    # Inworld voices (placeholder)
    if not provider or provider == "inworld":
        inworld_voices = [
            VoiceInfo(voice_id="inworld_male_1", name="Atlas", provider="inworld", gender="male", language="en", description="Character voice"),
            VoiceInfo(voice_id="inworld_female_1", name="Luna", provider="inworld", gender="female", language="en", description="Character voice"),
        ]
        voices.extend(inworld_voices)

    return voices


# ============================================================================
# SYSTEM ENDPOINTS
# ============================================================================

@app.get(
    "/queue/status",
    response_model=QueueStatusResponse,
    summary="Get Queue Status",
    tags=["System"],
)
async def queue_status() -> QueueStatusResponse:
    """Get current job queue status"""
    status_data = get_queue_status()
    return QueueStatusResponse(**status_data)


# ============================================================================
# APPLICATION LIFECYCLE
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Start background worker"""
    print("🚀 Rohimaya Audiobook Engine API starting...")
    print(f"📝 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"🔗 CORS Origins: {ALLOWED_ORIGINS}")

    # Start background worker
    asyncio.create_task(worker_loop())
    print("👷 Background worker started")
    print("✅ API ready")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("🛑 Rohimaya Audiobook Engine API shutting down...")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("ENVIRONMENT", "development") == "development"

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
