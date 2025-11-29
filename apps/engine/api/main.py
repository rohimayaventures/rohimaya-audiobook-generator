"""
AuthorFlow Studios - FastAPI Application
Production HTTP API for audiobook generation
"""

import os
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, status, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from .database import db
from .auth import get_current_user
from .worker import enqueue_job, worker_loop, get_queue_status, recover_pending_jobs, get_worker_health, is_worker_running
from .billing.routes import router as billing_router
from .billing.webhook import router as billing_webhook_router
from .billing.entitlements import get_plan_entitlements, PlanId
from .google_drive import (
    GoogleDriveClient,
    get_oauth_url,
    exchange_code_for_tokens,
    refresh_access_token,
    is_google_drive_configured,
)

# Load environment variables (Railway provides these directly, .env is for local dev)
env_path = Path(__file__).parent.parent.parent.parent / "env" / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

# Admin emails (comma-separated) - these users bypass billing limits
ADMIN_EMAILS = [email.strip().lower() for email in os.getenv("ADMIN_EMAILS", "").split(",") if email.strip()]

# Initialize FastAPI app
app = FastAPI(
    title="AuthorFlow Studios API",
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
# HELPER FUNCTIONS
# ============================================================================

def is_user_admin(user_info: Optional[Dict[str, Any]]) -> bool:
    """
    Check if user has admin privileges.

    Admin status can be granted via:
    1. user_metadata.role == "admin" in Supabase
    2. Email in ADMIN_EMAILS environment variable
    """
    if not user_info:
        return False

    # Check user_metadata for role
    user_metadata = user_info.get("user_metadata", {}) or {}
    if user_metadata.get("role") == "admin":
        return True

    # Check email against admin list
    user_email = (user_info.get("email") or "").lower()
    if user_email and user_email in ADMIN_EMAILS:
        return True

    return False


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
    source_type: str = Field(..., description="upload, paste, or google_drive")
    source_path: Optional[str] = Field(None, description="Storage path if uploaded, null if pasted")
    manuscript_text: Optional[str] = Field(None, description="Text content if pasted")
    mode: str = Field(..., description="single_voice, dual_voice, or findaway")
    tts_provider: str = Field(..., description="openai (elevenlabs and inworld coming soon)")
    narrator_voice_id: str = Field(..., description="Voice ID for narrator")
    character_voice_id: Optional[str] = Field(None, description="Voice ID for character (dual-voice only)")
    character_name: Optional[str] = Field(None, description="Character name (dual-voice only)")
    audio_format: str = Field(default="mp3", description="mp3, wav, flac, or m4b")
    audio_bitrate: str = Field(default="128k", description="128k, 192k, or 320k")

    # Findaway package options
    narrator_name: Optional[str] = Field(None, description="Narrator name for credits (findaway)")
    genre: Optional[str] = Field(None, description="Book genre (findaway)")
    language: Optional[str] = Field(default="en", description="Language code (findaway)")
    isbn: Optional[str] = Field(None, description="ISBN (findaway)")
    publisher: Optional[str] = Field(None, description="Publisher name (findaway)")
    sample_style: Optional[str] = Field(default="default", description="'default' or 'spicy' for romance (findaway)")

    # Cover art generation options
    generate_cover: bool = Field(default=False, description="Generate AI cover art for this audiobook")
    cover_vibe: Optional[str] = Field(None, description="Visual vibe for AI cover generation")
    cover_description: Optional[str] = Field(None, description="Custom description for cover art (user's vision)")
    cover_image_provider: Optional[str] = Field(None, description="openai or banana (uses env default if not set)")

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
    author: Optional[str] = None
    source_type: Optional[str] = None
    source_path: Optional[str] = None
    tts_provider: Optional[str] = None
    narrator_voice_id: Optional[str] = None
    character_voice_id: Optional[str] = None
    character_name: Optional[str] = None
    audio_format: Optional[str] = None
    audio_bitrate: Optional[str] = None
    audio_path: Optional[str] = None
    duration_seconds: Optional[int] = None
    file_size_bytes: Optional[int] = None
    progress_percent: Optional[float] = None
    current_step: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: Optional[int] = 0
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    # Findaway-specific fields
    narrator_name: Optional[str] = None
    genre: Optional[str] = None
    language: Optional[str] = None
    isbn: Optional[str] = None
    publisher: Optional[str] = None
    sample_style: Optional[str] = None
    package_type: Optional[str] = None
    section_count: Optional[int] = None

    # Cover art fields
    generate_cover: Optional[bool] = None
    cover_vibe: Optional[str] = None
    cover_image_provider: Optional[str] = None
    has_cover: Optional[bool] = None
    cover_image_path: Optional[str] = None


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
        service="authorflow-engine",
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
    # Validate source_type
    if request.source_type not in ["upload", "paste", "google_drive"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Source type '{request.source_type}' is not supported. "
                   f"Supported types: 'upload', 'paste', or 'google_drive'."
        )

    # Validate mode
    if request.mode not in ["single_voice", "dual_voice", "findaway"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mode must be 'single_voice', 'dual_voice', or 'findaway'"
        )

    # Validate TTS provider - only OpenAI is currently implemented
    if request.tts_provider not in ["openai"]:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"TTS provider '{request.tts_provider}' is not yet implemented. "
                   f"Currently supported: 'openai'. ElevenLabs and Inworld coming soon."
        )

    # Validate dual-voice requirements
    if request.mode == "dual_voice":
        if not request.character_voice_id or not request.character_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dual-voice mode requires character_voice_id and character_name"
            )

    # ==========================================================================
    # BILLING: Check plan limits before creating job
    # ==========================================================================

    # Get user info to check for admin role
    user_info = db.get_user(user_id)
    is_admin = is_user_admin(user_info)

    if not is_admin:
        # Get user's billing info
        billing_info = db.get_user_billing(user_id)
        plan_id = billing_info.get("plan_id", "free") if billing_info else "free"
        subscription_status = billing_info.get("status", "inactive") if billing_info else "inactive"

        # Check subscription status - block if trial expired or subscription canceled
        # Valid statuses that allow access: active, trialing
        # Invalid statuses: past_due, canceled, unpaid, inactive
        if plan_id != "free" and subscription_status not in ("active", "trialing"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Your subscription is {subscription_status}. Please update your payment method or resubscribe to continue creating audiobooks."
            )

        # Get plan entitlements
        entitlements = get_plan_entitlements(plan_id)

        # Check if user can create more projects this period
        if entitlements.max_projects_per_month is not None:
            usage = db.get_user_usage_current_period(user_id)
            current_projects = usage.get("projects_created", 0) if usage else 0

            if current_projects >= entitlements.max_projects_per_month:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Plan limit reached: {plan_id.title()} plan allows {entitlements.max_projects_per_month} projects per month. "
                           f"Please upgrade your plan to create more audiobooks."
                )

        # Check if Findaway mode is allowed
        if request.mode == "findaway" and not entitlements.findaway_package:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Findaway packages are not available on the Free plan. Please upgrade to Creator or higher."
            )

        # Check if dual-voice is allowed
        if request.mode == "dual_voice" and not entitlements.dual_voice:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Dual-voice narration is only available on Author Pro or higher plans."
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
        # Findaway-specific fields
        "narrator_name": request.narrator_name,
        "genre": request.genre,
        "language": request.language,
        "isbn": request.isbn,
        "publisher": request.publisher,
        "sample_style": request.sample_style,
        # Cover art generation
        "generate_cover": request.generate_cover,
        "cover_vibe": request.cover_vibe,
        "cover_description": request.cover_description,
        "cover_image_provider": request.cover_image_provider,
    }

    job = db.create_job(job_data)

    # Increment usage counter (for non-admin users)
    if not is_admin:
        try:
            db.increment_user_usage(user_id, projects=1, minutes=0)
        except Exception as e:
            # Log but don't fail - usage tracking shouldn't block job creation
            print(f"Warning: Failed to increment usage for user {user_id}: {e}")

    # Enqueue job for processing
    await enqueue_job(job["id"])

    return JobResponse(**job)


@app.post(
    "/jobs/upload",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Audiobook Job with File Upload",
    tags=["Jobs"],
)
async def create_job_with_upload(
    file: UploadFile = File(..., description="Manuscript file (TXT, DOCX, PDF)"),
    title: str = Form(..., description="Audiobook title"),
    source_type: str = Form(default="upload", description="Source type"),
    mode: str = Form(default="single_voice", description="Processing mode"),
    tts_provider: str = Form(default="openai", description="TTS provider"),
    narrator_voice_id: str = Form(default="alloy", description="Narrator voice ID"),
    audio_format: str = Form(default="mp3", description="Output audio format"),
    audio_bitrate: str = Form(default="128k", description="Audio bitrate"),
    user_id: str = Depends(get_current_user)
) -> JobResponse:
    """
    Create a new audiobook generation job with file upload.

    This endpoint accepts multipart/form-data for file uploads.
    The file will be stored in R2 and the job queued for processing.

    Requires authentication.
    """
    # Validate mode
    if mode not in ["single_voice", "dual_voice", "findaway"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mode must be 'single_voice', 'dual_voice', or 'findaway'"
        )

    # Validate TTS provider
    if tts_provider not in ["openai"]:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"TTS provider '{tts_provider}' is not yet implemented. Currently supported: 'openai'."
        )

    # Validate file type
    allowed_extensions = ['.txt', '.docx', '.pdf', '.md']
    file_ext = Path(file.filename).suffix.lower() if file.filename else ''
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )

    # ==========================================================================
    # BILLING: Check plan limits before creating job
    # ==========================================================================
    user_info = db.get_user(user_id)
    is_admin = is_user_admin(user_info)

    if not is_admin:
        billing_info = db.get_user_billing(user_id)
        plan_id = billing_info.get("plan_id", "free") if billing_info else "free"
        subscription_status = billing_info.get("status", "inactive") if billing_info else "inactive"

        # Check subscription status - block if trial expired or subscription canceled
        if plan_id != "free" and subscription_status not in ("active", "trialing"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Your subscription is {subscription_status}. Please update your payment method or resubscribe to continue creating audiobooks."
            )

        entitlements = get_plan_entitlements(plan_id)

        if entitlements.max_projects_per_month is not None:
            usage = db.get_user_usage_current_period(user_id)
            current_projects = usage.get("projects_created", 0) if usage else 0

            if current_projects >= entitlements.max_projects_per_month:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Plan limit reached: {plan_id.title()} plan allows {entitlements.max_projects_per_month} projects per month. "
                           f"Please upgrade your plan to create more audiobooks."
                )

        if mode == "findaway" and not entitlements.findaway_package:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Findaway packages are not available on the Free plan. Please upgrade to Creator or higher."
            )

    # Read file content
    try:
        file_content = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read file: {str(e)}"
        )

    # Upload to R2 storage
    try:
        source_path = db.upload_manuscript(
            user_id=user_id,
            filename=file.filename or "manuscript.txt",
            file_content=file_content
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )

    # Create job in database
    job_data = {
        "user_id": user_id,
        "status": "pending",
        "mode": mode,
        "title": title,
        "source_type": "upload",
        "source_path": source_path,
        "tts_provider": tts_provider,
        "narrator_voice_id": narrator_voice_id,
        "audio_format": audio_format,
        "audio_bitrate": audio_bitrate,
        "progress_percent": 0.0,
    }

    job = db.create_job(job_data)

    # Increment usage counter
    if not is_admin:
        try:
            db.increment_user_usage(user_id, projects=1, minutes=0)
        except Exception as e:
            print(f"Warning: Failed to increment usage for user {user_id}: {e}")

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


class DownloadUrlResponse(BaseModel):
    """Response containing presigned download URL"""
    url: str
    expires_in: int = 3600


@app.get(
    "/jobs/{job_id}/download",
    response_model=DownloadUrlResponse,
    summary="Get Download URL",
    tags=["Jobs"],
)
async def get_download_url(
    job_id: str,
    user_id: str = Depends(get_current_user)
) -> DownloadUrlResponse:
    """
    Get presigned download URL for completed audiobook

    Returns a JSON object with the signed URL (expires in 1 hour).
    Use this URL directly in audio players and download links.
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

    # Check if audio_path exists
    if not job.get("audio_path"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found for this job"
        )

    # Get signed download URL
    download_url = db.get_download_url(job["audio_path"], expires_in=3600)

    return DownloadUrlResponse(url=download_url, expires_in=3600)


@app.post(
    "/jobs/{job_id}/retry",
    response_model=JobResponse,
    summary="Retry Failed Job",
    tags=["Jobs"],
)
async def retry_job(
    job_id: str,
    user_id: str = Depends(get_current_user)
) -> JobResponse:
    """
    Retry a failed job

    Resets the job status to 'pending' and re-enqueues it for processing.
    Only works on jobs with status 'failed'.

    Requires authentication. User can only retry their own jobs.
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
            detail="You do not have permission to retry this job"
        )

    # Only allow retrying failed or cancelled jobs
    if job["status"] not in ["failed", "cancelled"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Can only retry failed or cancelled jobs (current status: {job['status']})"
        )

    # Track retry count (no limit for now during development)
    current_retry_count = job.get("retry_count", 0)

    # Reset job for retry
    updates = {
        "status": "pending",
        "error_message": None,
        "progress_percent": 0.0,
        "current_step": None,
        "started_at": None,
        "completed_at": None,
        "retry_count": current_retry_count + 1,
    }

    # Update job in database
    updated_job = db.update_job(job_id, updates)

    # Re-enqueue for processing
    await enqueue_job(job_id)

    return JobResponse(**updated_job)


@app.post(
    "/jobs/{job_id}/cancel",
    response_model=JobResponse,
    summary="Cancel Job",
    tags=["Jobs"],
)
async def cancel_job(
    job_id: str,
    user_id: str = Depends(get_current_user)
) -> JobResponse:
    """
    Cancel a pending or processing job.

    Sets the job status to 'cancelled'. The background worker will stop
    processing the job when it checks the status.

    Requires authentication. User can only cancel their own jobs.
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
            detail="You do not have permission to cancel this job"
        )

    # Only allow cancelling pending or processing jobs
    if job["status"] not in ["pending", "processing"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Can only cancel pending or processing jobs (current status: {job['status']})"
        )

    # Update job status to cancelled
    updates = {
        "status": "cancelled",
        "error_message": "Job cancelled by user",
        "completed_at": datetime.utcnow().isoformat(),
    }

    updated_job = db.update_job(job_id, updates)

    logger.info(f"[JOB] {job_id} - Cancelled by user")

    return JobResponse(**updated_job)


class CloneJobRequest(BaseModel):
    """Request to clone a job with optional modifications"""
    title: Optional[str] = Field(None, description="New title (or keep original)")
    narrator_voice_id: Optional[str] = Field(None, description="New narrator voice (or keep original)")
    mode: Optional[str] = Field(None, description="New mode (or keep original)")


@app.post(
    "/jobs/{job_id}/clone",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Clone Job",
    tags=["Jobs"],
)
async def clone_job(
    job_id: str,
    request: Optional[CloneJobRequest] = None,
    user_id: str = Depends(get_current_user)
) -> JobResponse:
    """
    Clone an existing job with optional modifications.

    Creates a new job based on an existing one, copying:
    - Source manuscript (source_path)
    - Title, author, and metadata
    - Voice and audio settings

    Optionally override: title, narrator_voice_id, mode

    The new job will be queued for processing immediately.

    Requires authentication. User can only clone their own jobs.
    """
    # Get original job
    original_job = db.get_job(job_id)

    if not original_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )

    # Verify ownership
    if original_job["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to clone this job"
        )

    # Build new job data from original
    new_job_data = {
        "user_id": user_id,
        "status": "pending",
        # Copy from original (required fields)
        "title": original_job.get("title", "Untitled"),
        "source_type": original_job.get("source_type", "upload"),
        "source_path": original_job.get("source_path"),
        "mode": original_job.get("mode", "single_voice"),
        "tts_provider": original_job.get("tts_provider", "openai"),
        "narrator_voice_id": original_job.get("narrator_voice_id", "alloy"),
        # Copy optional fields
        "author": original_job.get("author"),
        "character_voice_id": original_job.get("character_voice_id"),
        "character_name": original_job.get("character_name"),
        "audio_format": original_job.get("audio_format", "mp3"),
        "audio_bitrate": original_job.get("audio_bitrate", "128k"),
        "narrator_name": original_job.get("narrator_name"),
        "genre": original_job.get("genre"),
        "language": original_job.get("language", "en"),
        "isbn": original_job.get("isbn"),
        "publisher": original_job.get("publisher"),
        "sample_style": original_job.get("sample_style", "default"),
        "cover_vibe": original_job.get("cover_vibe"),
        # Reset progress fields
        "progress_percent": 0.0,
        "retry_count": 0,
    }

    # Apply overrides from request
    if request:
        if request.title:
            new_job_data["title"] = request.title
        if request.narrator_voice_id:
            new_job_data["narrator_voice_id"] = request.narrator_voice_id
        if request.mode:
            # Validate mode
            if request.mode not in ["single_voice", "dual_voice", "findaway", "multi_character"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid mode. Must be: single_voice, dual_voice, findaway, or multi_character"
                )
            new_job_data["mode"] = request.mode

    # Add clone metadata
    new_job_data["title"] = f"{new_job_data['title']} (Clone)"

    # Create new job
    new_job = db.create_job(new_job_data)

    # Enqueue for processing
    await enqueue_job(new_job["id"])

    return JobResponse(**new_job)


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
    # Wrap in try-except to ensure job deletion succeeds even if storage cleanup fails
    # (e.g., files from old bucket naming convention or already deleted files)
    try:
        if job["source_path"]:
            db.delete_storage_file("manuscripts", job["source_path"])
    except Exception as e:
        print(f"⚠️ Failed to delete manuscript for job {job_id}: {e}")

    try:
        if job["audio_path"]:
            db.delete_storage_file("audiobooks", job["audio_path"])
    except Exception as e:
        print(f"⚠️ Failed to delete audiobook for job {job_id}: {e}")

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
# INCLUDE BILLING ROUTERS
# ============================================================================

app.include_router(billing_router)
app.include_router(billing_webhook_router)


# ============================================================================
# GOOGLE DRIVE INTEGRATION ENDPOINTS
# ============================================================================

class GoogleDriveAuthUrlResponse(BaseModel):
    """Google Drive OAuth URL response"""
    url: str
    state: str


class GoogleDriveFileInfo(BaseModel):
    """Google Drive file information"""
    id: str
    name: str
    mime_type: str
    size: Optional[int] = None
    created_time: Optional[str] = None
    modified_time: Optional[str] = None
    icon_link: Optional[str] = None
    web_view_link: Optional[str] = None


class GoogleDriveFilesResponse(BaseModel):
    """Google Drive files list response"""
    files: List[GoogleDriveFileInfo]
    next_page_token: Optional[str] = None


class GoogleDriveImportResponse(BaseModel):
    """Google Drive import result"""
    source_type: str = "google_drive"
    source_path: str
    title: str
    word_count: int
    file_size_bytes: int


@app.get(
    "/google-drive/auth-url",
    response_model=GoogleDriveAuthUrlResponse,
    summary="Get Google Drive OAuth URL",
    tags=["Google Drive"],
)
async def get_google_drive_auth_url(
    user_id: str = Depends(get_current_user)
) -> GoogleDriveAuthUrlResponse:
    """
    Get the Google OAuth authorization URL.

    The frontend should redirect the user to this URL to complete Google Drive authorization.
    After authorization, Google will redirect back to the callback URL with an authorization code.
    """
    if not is_google_drive_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google Drive integration is not configured. Contact support."
        )

    import secrets
    state = f"{user_id}:{secrets.token_urlsafe(16)}"

    try:
        auth_url = get_oauth_url(state=state)
        return GoogleDriveAuthUrlResponse(url=auth_url, state=state)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate auth URL: {str(e)}"
        )


@app.get(
    "/google-drive/callback",
    summary="Google Drive OAuth Callback",
    tags=["Google Drive"],
)
async def google_drive_oauth_callback(
    code: str,
    state: str,
    error: Optional[str] = None,
):
    """
    Handle Google OAuth callback.

    This endpoint is called by Google after the user authorizes access.
    It exchanges the authorization code for access tokens and stores them.
    Then redirects back to the frontend with success/failure status.
    """
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

    if error:
        return RedirectResponse(
            url=f"{frontend_url}/dashboard?googleDrive=error&message={error}"
        )

    # Extract user_id from state
    try:
        user_id = state.split(":")[0]
    except:
        return RedirectResponse(
            url=f"{frontend_url}/dashboard?googleDrive=error&message=invalid_state"
        )

    try:
        # Exchange code for tokens
        tokens = await exchange_code_for_tokens(code)

        # Store tokens in database (in user's google_drive_tokens)
        db.store_google_drive_tokens(user_id, {
            "access_token": tokens.get("access_token"),
            "refresh_token": tokens.get("refresh_token"),
            "expires_in": tokens.get("expires_in"),
            "token_type": tokens.get("token_type"),
        })

        return RedirectResponse(
            url=f"{frontend_url}/dashboard?googleDrive=connected"
        )
    except Exception as e:
        print(f"Google Drive OAuth error: {e}")
        return RedirectResponse(
            url=f"{frontend_url}/dashboard?googleDrive=error&message=token_exchange_failed"
        )


@app.get(
    "/google-drive/status",
    summary="Check Google Drive connection status",
    tags=["Google Drive"],
)
async def get_google_drive_status(
    user_id: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Check if the user has connected their Google Drive.
    """
    if not is_google_drive_configured():
        return {
            "configured": False,
            "connected": False,
            "message": "Google Drive integration is not configured on this server."
        }

    tokens = db.get_google_drive_tokens(user_id)
    connected = tokens is not None and tokens.get("access_token") is not None

    return {
        "configured": True,
        "connected": connected,
    }


@app.get(
    "/google-drive/files",
    response_model=GoogleDriveFilesResponse,
    summary="List Google Drive Files",
    tags=["Google Drive"],
)
async def list_google_drive_files(
    user_id: str = Depends(get_current_user),
    page_token: Optional[str] = None,
    page_size: int = 20,
) -> GoogleDriveFilesResponse:
    """
    List files from the user's Google Drive that are suitable as manuscripts.

    Returns Google Docs, DOCX, PDF, and TXT files, sorted by most recently modified.
    """
    if not is_google_drive_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google Drive integration is not configured."
        )

    # Get user's tokens
    tokens = db.get_google_drive_tokens(user_id)
    if not tokens or not tokens.get("access_token"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google Drive not connected. Please authorize first."
        )

    try:
        client = GoogleDriveClient(tokens["access_token"])
        result = await client.list_files(page_size=page_size, page_token=page_token)

        files = [
            GoogleDriveFileInfo(
                id=f["id"],
                name=f["name"],
                mime_type=f.get("mimeType", ""),
                size=int(f["size"]) if f.get("size") else None,
                created_time=f.get("createdTime"),
                modified_time=f.get("modifiedTime"),
                icon_link=f.get("iconLink"),
                web_view_link=f.get("webViewLink"),
            )
            for f in result.get("files", [])
        ]

        return GoogleDriveFilesResponse(
            files=files,
            next_page_token=result.get("nextPageToken")
        )
    except Exception as e:
        # Check if it's a token error
        error_str = str(e).lower()
        if "401" in error_str or "unauthorized" in error_str or "invalid" in error_str:
            # Try to refresh the token
            if tokens.get("refresh_token"):
                try:
                    new_tokens = await refresh_access_token(tokens["refresh_token"])
                    db.store_google_drive_tokens(user_id, {
                        **tokens,
                        "access_token": new_tokens.get("access_token"),
                    })
                    # Retry with new token
                    client = GoogleDriveClient(new_tokens["access_token"])
                    result = await client.list_files(page_size=page_size, page_token=page_token)
                    files = [
                        GoogleDriveFileInfo(
                            id=f["id"],
                            name=f["name"],
                            mime_type=f.get("mimeType", ""),
                            size=int(f["size"]) if f.get("size") else None,
                            created_time=f.get("createdTime"),
                            modified_time=f.get("modifiedTime"),
                            icon_link=f.get("iconLink"),
                            web_view_link=f.get("webViewLink"),
                        )
                        for f in result.get("files", [])
                    ]
                    return GoogleDriveFilesResponse(
                        files=files,
                        next_page_token=result.get("nextPageToken")
                    )
                except Exception as refresh_error:
                    # Clear tokens and require re-auth
                    db.clear_google_drive_tokens(user_id)
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Google Drive authorization expired. Please reconnect."
                    )
            else:
                db.clear_google_drive_tokens(user_id)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Google Drive authorization expired. Please reconnect."
                )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list Google Drive files: {str(e)}"
        )


class GoogleDriveImportRequest(BaseModel):
    """Request to import a file from Google Drive"""
    file_id: str


@app.post(
    "/google-drive/import",
    response_model=GoogleDriveImportResponse,
    summary="Import File from Google Drive",
    tags=["Google Drive"],
)
async def import_google_drive_file(
    request: GoogleDriveImportRequest,
    user_id: str = Depends(get_current_user),
) -> GoogleDriveImportResponse:
    """
    Import a file from Google Drive as a manuscript.

    Downloads the file, converts it to text, and uploads it to R2 storage.
    Returns the storage path that can be used to create a job.
    """
    if not is_google_drive_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google Drive integration is not configured."
        )

    # Get user's tokens
    tokens = db.get_google_drive_tokens(user_id)
    if not tokens or not tokens.get("access_token"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google Drive not connected. Please authorize first."
        )

    try:
        client = GoogleDriveClient(tokens["access_token"])

        # Get file metadata
        file_metadata = await client.get_file_metadata(request.file_id)
        file_name = file_metadata.get("name", "Untitled")
        mime_type = file_metadata.get("mimeType", "")

        # Validate mime type
        supported_types = [
            "application/vnd.google-apps.document",
            "text/plain",
            "text/markdown",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/pdf",
            "application/rtf",
        ]

        if mime_type not in supported_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {mime_type}. "
                       f"Supported types: Google Docs, TXT, DOCX, PDF, RTF"
            )

        # Download and convert to text
        text_content = await client.download_file_as_text(request.file_id, mime_type)

        if not text_content or not text_content.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The file appears to be empty or could not be converted to text."
            )

        # Upload to R2 storage
        filename = f"{file_name.replace(' ', '_')}.txt"
        source_path = db.upload_manuscript(
            user_id=user_id,
            filename=filename,
            file_content=text_content.encode("utf-8")
        )

        # Calculate metrics
        word_count = len(text_content.split())
        file_size_bytes = len(text_content.encode("utf-8"))

        return GoogleDriveImportResponse(
            source_type="google_drive",
            source_path=source_path,
            title=file_name.replace(".docx", "").replace(".pdf", "").replace(".txt", ""),
            word_count=word_count,
            file_size_bytes=file_size_bytes,
        )

    except HTTPException:
        raise
    except Exception as e:
        error_str = str(e).lower()
        if "401" in error_str or "unauthorized" in error_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google Drive authorization expired. Please reconnect."
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import file: {str(e)}"
        )


@app.delete(
    "/google-drive/disconnect",
    summary="Disconnect Google Drive",
    tags=["Google Drive"],
)
async def disconnect_google_drive(
    user_id: str = Depends(get_current_user),
) -> Dict[str, str]:
    """
    Disconnect Google Drive integration for the current user.
    Removes stored tokens.
    """
    db.clear_google_drive_tokens(user_id)
    return {"message": "Google Drive disconnected successfully"}


# ============================================================================
# COVER ART ENDPOINTS
# ============================================================================

class CoverArtResponse(BaseModel):
    """Cover art response"""
    has_cover: bool
    cover_url: Optional[str] = None
    cover_path: Optional[str] = None


@app.get(
    "/jobs/{job_id}/cover",
    response_model=CoverArtResponse,
    summary="Get Cover Image URL",
    tags=["Jobs"],
)
async def get_job_cover_url(
    job_id: str,
    user_id: str = Depends(get_current_user)
) -> CoverArtResponse:
    """
    Get cover art information for a job.

    Returns has_cover=false if no cover is available.
    If has_cover=true, cover_url contains a presigned URL (expires in 1 hour).
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

    # Check if job has a cover
    if not job.get("has_cover") or not job.get("cover_image_path"):
        return CoverArtResponse(has_cover=False)

    # Get presigned URL
    try:
        cover_url = db.get_download_url(job["cover_image_path"], expires_in=3600)
        return CoverArtResponse(
            has_cover=True,
            cover_url=cover_url,
            cover_path=job.get("cover_image_path")
        )
    except Exception as e:
        print(f"Failed to generate cover URL for job {job_id}: {e}")
        return CoverArtResponse(has_cover=False)


# ============================================================================
# WORKER HEALTH ENDPOINT
# ============================================================================

class WorkerHealthResponse(BaseModel):
    """Worker health status"""
    worker_running: bool
    queued_jobs: int
    processing_jobs: int
    processing_job_ids: List[str]
    total_jobs: int
    pydub_available: bool
    temp_directory: str


@app.get(
    "/worker/health",
    response_model=WorkerHealthResponse,
    summary="Worker Health Check",
    tags=["System"],
)
async def worker_health() -> WorkerHealthResponse:
    """
    Get background worker health status.

    This endpoint does NOT require authentication and can be used for monitoring.

    Returns:
    - worker_running: Whether the worker loop is active
    - queued_jobs: Number of jobs waiting in queue
    - processing_jobs: Number of jobs currently being processed
    - processing_job_ids: List of job IDs currently being processed
    - total_jobs: Total jobs in queue + processing
    """
    health = get_worker_health()
    return WorkerHealthResponse(**health)


# ============================================================================
# ADMIN SYSTEM STATUS PANEL
# ============================================================================

class SystemStatusResponse(BaseModel):
    """Complete system status for admin panel"""
    # API Status
    api_version: str
    environment: str
    uptime_seconds: Optional[int] = None

    # Worker Status
    worker_running: bool
    queued_jobs: int
    processing_jobs: int
    processing_job_ids: List[str]

    # Database Stats
    total_jobs: int
    pending_jobs: int
    processing_jobs_db: int
    completed_jobs: int
    failed_jobs: int

    # User Stats
    total_users: int
    active_subscriptions: int

    # Feature Flags
    google_drive_enabled: bool
    emotional_tts_enabled: bool
    banana_cover_enabled: bool

    # Recent Errors
    recent_errors: List[Dict[str, Any]]


@app.get(
    "/admin/status",
    response_model=SystemStatusResponse,
    summary="System Status Panel (Admin Only)",
    tags=["Admin"],
)
async def get_system_status(
    user_id: str = Depends(get_current_user)
) -> SystemStatusResponse:
    """
    Get complete system status for admin dashboard.

    Requires authentication and admin role.

    Returns comprehensive system information including:
    - API and worker status
    - Job statistics
    - User statistics
    - Feature flag status
    - Recent errors
    """
    # Check admin role
    user_info = db.get_user(user_id)
    is_admin = is_user_admin(user_info)

    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    # Get worker health
    worker_health_data = get_worker_health()

    # Get job statistics from database
    try:
        job_stats = db.client.table("jobs").select("status", count="exact").execute()

        # Count by status
        all_jobs = db.client.table("jobs").select("id, status").execute()
        status_counts = {"pending": 0, "processing": 0, "completed": 0, "failed": 0}
        for job in all_jobs.data or []:
            job_status = job.get("status", "unknown")
            if job_status in status_counts:
                status_counts[job_status] += 1

        total_jobs = len(all_jobs.data) if all_jobs.data else 0
    except Exception as e:
        print(f"Error fetching job stats: {e}")
        total_jobs = 0
        status_counts = {"pending": 0, "processing": 0, "completed": 0, "failed": 0}

    # Get user statistics
    try:
        # Count users with active billing
        billing_data = db.client.table("user_billing").select("id, status").execute()
        active_subs = len([b for b in (billing_data.data or []) if b.get("status") == "active"])

        # Count total users (estimate from billing records)
        total_users = len(billing_data.data) if billing_data.data else 0
    except Exception as e:
        print(f"Error fetching user stats: {e}")
        total_users = 0
        active_subs = 0

    # Get recent errors (last 10 failed jobs)
    try:
        failed_jobs = db.client.table("jobs").select(
            "id, title, error_message, completed_at"
        ).eq("status", "failed").order(
            "completed_at", desc=True
        ).limit(10).execute()

        recent_errors = [
            {
                "job_id": job.get("id"),
                "title": job.get("title"),
                "error": job.get("error_message"),
                "timestamp": job.get("completed_at"),
            }
            for job in (failed_jobs.data or [])
        ]
    except Exception as e:
        print(f"Error fetching recent errors: {e}")
        recent_errors = []

    # Check feature flags
    from .google_drive import is_google_drive_configured

    return SystemStatusResponse(
        # API Status
        api_version="0.3.0",
        environment=os.getenv("ENVIRONMENT", "development"),
        uptime_seconds=None,  # Would need to track startup time

        # Worker Status
        worker_running=worker_health_data.get("worker_running", False),
        queued_jobs=worker_health_data.get("queued_jobs", 0),
        processing_jobs=worker_health_data.get("processing_jobs", 0),
        processing_job_ids=worker_health_data.get("processing_job_ids", []),

        # Database Stats
        total_jobs=total_jobs,
        pending_jobs=status_counts["pending"],
        processing_jobs_db=status_counts["processing"],
        completed_jobs=status_counts["completed"],
        failed_jobs=status_counts["failed"],

        # User Stats
        total_users=total_users,
        active_subscriptions=active_subs,

        # Feature Flags
        google_drive_enabled=is_google_drive_configured(),
        emotional_tts_enabled=os.getenv("EMOTIONAL_TTS_ENABLED", "true").lower() == "true",
        banana_cover_enabled=bool(os.getenv("BANANA_API_KEY")),

        # Recent Errors
        recent_errors=recent_errors,
    )


# ============================================================================
# DEBUG/SELF-TEST ENDPOINT (Disabled by default in production)
# ============================================================================

# Enable with ENGINE_SELF_TEST_ENABLED=true
ENGINE_SELF_TEST_ENABLED = os.getenv("ENGINE_SELF_TEST_ENABLED", "false").lower() == "true"


class SelfTestResponse(BaseModel):
    """Response from self-test endpoint"""
    status: str  # "ok" | "failed"
    job_id: Optional[str] = None
    audio_files: List[str] = []
    final_path_exists: bool = False
    duration_seconds: int = 0
    error: Optional[str] = None
    test_mode: str = "stub"  # "stub" | "real_openai"
    details: Dict[str, Any] = {}


@app.post(
    "/debug/self-test",
    response_model=SelfTestResponse,
    tags=["Debug"],
    summary="Run pipeline self-test",
    description="""
    Debug endpoint to test the audiobook generation pipeline.
    Disabled by default - enable with ENGINE_SELF_TEST_ENABLED=true.

    This endpoint:
    1. Creates a temporary job with a short test manuscript
    2. Runs the single-voice pipeline (stub or real OpenAI)
    3. Returns detailed results for debugging
    """,
)
async def run_self_test(
    use_real_tts: bool = False,
    user_id: str = Depends(get_current_user),
):
    """
    Run a self-test of the audiobook pipeline.

    Args:
        use_real_tts: If true, use real OpenAI TTS (costs money). If false, generate stub audio.
    """
    import tempfile
    import uuid
    from pathlib import Path

    # Check if self-test is enabled
    if not ENGINE_SELF_TEST_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Self-test endpoint is disabled. Set ENGINE_SELF_TEST_ENABLED=true to enable."
        )

    test_job_id = f"test-{uuid.uuid4().hex[:8]}"
    test_manuscript = """
    Chapter 1: The Beginning

    This is a short test manuscript for the audiobook pipeline self-test.
    It contains enough text to verify the TTS system is working correctly.

    The quick brown fox jumps over the lazy dog. This sentence contains
    every letter of the alphabet and is commonly used for testing.

    Chapter 2: The End

    This concludes our brief test. If you can hear this, the pipeline works!
    """

    output_dir = None
    result = SelfTestResponse(
        status="failed",
        job_id=test_job_id,
        test_mode="real_openai" if use_real_tts else "stub",
    )

    try:
        # Create temp directory
        output_dir = Path(tempfile.gettempdir()) / "authorflow_selftest" / test_job_id
        output_dir.mkdir(parents=True, exist_ok=True)
        result.details["output_dir"] = str(output_dir)

        if use_real_tts:
            # Use real OpenAI TTS
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not configured")

            from pipelines.standard_single_voice import generate_single_voice_audiobook

            audio_files = generate_single_voice_audiobook(
                manuscript_text=test_manuscript,
                output_dir=output_dir,
                api_key=api_key,
                voice_id="alloy",
                tts_provider="openai",
                book_title="SelfTest",
            )

            result.audio_files = [str(f) for f in audio_files]
            result.final_path_exists = len(audio_files) > 0 and Path(audio_files[-1]).exists()

            if result.final_path_exists:
                from .worker import get_audio_duration
                result.duration_seconds = get_audio_duration(Path(audio_files[-1]))

        else:
            # Stub mode - just verify imports and structure work
            try:
                from pipelines.standard_single_voice import SingleVoicePipeline
                from core.chapter_parser import split_into_chapters
                from core.advanced_chunker import chunk_chapter_advanced

                result.details["imports"] = "ok"

                # Parse chapters
                chapters = split_into_chapters(test_manuscript)
                result.details["chapters_parsed"] = len(chapters)

                # Chunk first chapter
                if chapters:
                    chunks = chunk_chapter_advanced(chapters[0]["text"], 700, 5000)
                    result.details["chunks_created"] = len(chunks)

                # Create stub audio file
                stub_audio_path = output_dir / "SelfTest_STUB.mp3"
                stub_audio_path.write_bytes(b"\x00" * 1000)  # Dummy bytes

                result.audio_files = [str(stub_audio_path)]
                result.final_path_exists = stub_audio_path.exists()
                result.details["stub_file_size"] = stub_audio_path.stat().st_size

            except ImportError as e:
                result.error = f"Import error: {e}"
                result.details["import_error"] = str(e)
                return result

        result.status = "ok" if result.final_path_exists else "failed"
        if not result.final_path_exists:
            result.error = "Final audio file was not created"

    except Exception as e:
        import traceback
        result.status = "failed"
        result.error = f"{type(e).__name__}: {str(e)}"
        result.details["traceback"] = traceback.format_exc()

    finally:
        # Clean up (optional - keep for debugging)
        # if output_dir and output_dir.exists():
        #     import shutil
        #     shutil.rmtree(output_dir)
        pass

    return result


# ============================================================================
# APPLICATION LIFECYCLE
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Start background worker and recover pending jobs"""
    print("🚀 AuthorFlow Studios API starting...")
    print(f"📝 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"🔗 CORS Origins: {ALLOWED_ORIGINS}")

    # Start background worker
    asyncio.create_task(worker_loop())
    print("👷 Background worker started")

    # Wait a moment for worker to initialize
    await asyncio.sleep(0.5)

    # Recover any pending/processing jobs from before restart
    print("🔄 Checking for jobs to recover...")
    recovery_result = await recover_pending_jobs()

    if recovery_result["total_recovered"] > 0:
        print(f"✅ Recovered {recovery_result['total_recovered']} jobs:")
        print(f"   - Pending: {recovery_result['recovered_pending']}")
        print(f"   - Interrupted: {recovery_result['recovered_processing']}")
        for job_id in recovery_result["recovered_job_ids"]:
            print(f"   - {job_id}")
    else:
        print("✅ No jobs to recover")

    if recovery_result["errors"]:
        print(f"⚠️ Recovery errors: {len(recovery_result['errors'])}")
        for error in recovery_result["errors"]:
            print(f"   - {error}")

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

    # Use api.main:app for proper package resolution
    # Run from apps/engine directory: python -m api.main
    # Or: cd apps/engine && uvicorn api.main:app
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
