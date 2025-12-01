"""
AuthorFlow Studios - FastAPI Application
Production HTTP API for audiobook generation
"""

import os
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

from fastapi import FastAPI, HTTPException, status, Depends, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse
import traceback
import uuid

logger = logging.getLogger(__name__)
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
from .rate_limiter import (
    limiter,
    rate_limit_exception_handler,
    check_job_creation_limit,
    get_job_creation_remaining,
    is_rate_limiting_enabled,
    RATE_LIMITS,
)
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

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

# Rate Limiting - add limiter to app state and exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ============================================================================
# GLOBAL EXCEPTION HANDLERS
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled errors.
    Logs the full traceback and returns a structured error response.
    """
    # Generate a unique error ID for tracking
    error_id = str(uuid.uuid4())[:8]

    # Log the full error with traceback
    logger.error(f"[ERROR-{error_id}] Unhandled exception on {request.method} {request.url.path}")
    logger.error(f"[ERROR-{error_id}] {type(exc).__name__}: {str(exc)}")
    logger.error(f"[ERROR-{error_id}] Traceback:\n{traceback.format_exc()}")

    # Return structured error response
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred. Please try again.",
            "error_id": error_id,
            "detail": str(exc) if os.getenv("ENVIRONMENT") != "production" else None,
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handler for HTTP exceptions - log 4xx/5xx errors for monitoring.
    """
    if exc.status_code >= 500:
        logger.error(f"[HTTP-{exc.status_code}] {request.method} {request.url.path}: {exc.detail}")
    elif exc.status_code >= 400:
        logger.warning(f"[HTTP-{exc.status_code}] {request.method} {request.url.path}: {exc.detail}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail if isinstance(exc.detail, str) else "error",
            "message": exc.detail,
        }
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

class DependencyHealth(BaseModel):
    """Health status of a single dependency"""
    name: str
    status: str  # "ok", "degraded", "error"
    latency_ms: Optional[float] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str
    timestamp: str
    dependencies: Optional[Dict[str, DependencyHealth]] = None
    worker_running: Optional[bool] = None
    queue_size: Optional[int] = None


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

    # Multilingual TTS options (Gemini TTS)
    input_language_code: Optional[str] = Field(default="en-US", description="Input language code for TTS (e.g., en-US, hi-IN)")
    output_language_code: Optional[str] = Field(None, description="Output language code - if different from input, text will be translated")
    voice_preset_id: Optional[str] = Field(None, description="Gemini voice preset ID (e.g., studio_neutral, romantic_female)")
    emotion_style_prompt: Optional[str] = Field(None, description="Emotion/style prompt for TTS (e.g., 'soft, romantic, intimate')")

    # Findaway package options
    narrator_name: Optional[str] = Field(None, description="Narrator name for credits (findaway)")
    genre: Optional[str] = Field(None, description="Book genre (findaway)")
    language: Optional[str] = Field(default="en", description="Language code (findaway)")
    isbn: Optional[str] = Field(None, description="ISBN (findaway)")
    publisher: Optional[str] = Field(None, description="Publisher name (findaway)")
    sample_style: Optional[str] = Field(default="default", description="'default' or 'spicy' for romance (findaway)")

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

    # Multilingual TTS fields (Gemini TTS)
    input_language_code: Optional[str] = None
    output_language_code: Optional[str] = None
    voice_preset_id: Optional[str] = None
    emotion_style_prompt: Optional[str] = None

    # Findaway-specific fields
    narrator_name: Optional[str] = None
    genre: Optional[str] = None
    language: Optional[str] = None
    isbn: Optional[str] = None
    publisher: Optional[str] = None
    sample_style: Optional[str] = None
    package_type: Optional[str] = None
    section_count: Optional[int] = None



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
async def health_check(detailed: bool = False) -> HealthResponse:
    """
    Health check endpoint for monitoring.

    Pass ?detailed=true for dependency health checks (Supabase, R2, Worker).
    """
    import time

    dependencies = {}
    overall_status = "ok"

    if detailed:
        # Check Supabase connection
        try:
            start = time.time()
            # Simple query to test connection
            db.client.table("jobs").select("id").limit(1).execute()
            latency = (time.time() - start) * 1000
            dependencies["supabase"] = DependencyHealth(
                name="supabase",
                status="ok",
                latency_ms=round(latency, 2)
            )
        except Exception as e:
            overall_status = "degraded"
            dependencies["supabase"] = DependencyHealth(
                name="supabase",
                status="error",
                error=str(e)[:100]
            )

        # Check R2 Storage connection
        try:
            start = time.time()
            # Just check if we can list buckets
            r2_url = os.getenv("R2_ENDPOINT_URL")
            if r2_url:
                # R2 client is initialized in database.py
                latency = (time.time() - start) * 1000
                dependencies["r2_storage"] = DependencyHealth(
                    name="r2_storage",
                    status="ok" if r2_url else "not_configured",
                    latency_ms=round(latency, 2)
                )
            else:
                dependencies["r2_storage"] = DependencyHealth(
                    name="r2_storage",
                    status="not_configured"
                )
        except Exception as e:
            overall_status = "degraded"
            dependencies["r2_storage"] = DependencyHealth(
                name="r2_storage",
                status="error",
                error=str(e)[:100]
            )

        # Check TTS provider availability
        google_key = os.getenv("GOOGLE_GENAI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        dependencies["tts"] = DependencyHealth(
            name="tts",
            status="ok" if (google_key or openai_key) else "not_configured",
            error=None if (google_key or openai_key) else "No TTS API key configured"
        )

    # Get worker and queue status
    queue_status = get_queue_status()
    worker_running = is_worker_running()

    if not worker_running:
        overall_status = "degraded"

    return HealthResponse(
        status=overall_status,
        service="authorflow-engine",
        version="0.2.0",
        timestamp=datetime.utcnow().isoformat() + "Z",
        dependencies=dependencies if detailed else None,
        worker_running=worker_running,
        queue_size=queue_status.get("total", 0)
    )


# ============================================================================
# RATE LIMIT STATUS ENDPOINT
# ============================================================================

class RateLimitStatusResponse(BaseModel):
    """Rate limit status for current user"""
    plan: str
    requests_per_minute: int
    jobs_per_hour: Optional[int]
    jobs_remaining_this_hour: Optional[int]
    rate_limiting_enabled: bool


@app.get(
    "/rate-limit/status",
    response_model=RateLimitStatusResponse,
    summary="Get Rate Limit Status",
    tags=["Rate Limiting"],
)
async def get_rate_limit_status(
    user_id: str = Depends(get_current_user)
) -> RateLimitStatusResponse:
    """
    Get current rate limit status for the authenticated user.

    Returns the user's plan limits and remaining quota.
    """
    # Get user's billing info
    billing_info = db.get_user_billing(user_id)
    plan_id = billing_info.get("plan_id", "free") if billing_info else "free"

    # Check if admin
    user_info = db.get_user(user_id)
    if is_user_admin(user_info):
        plan_id = "admin"

    # Get limits for plan
    limits = RATE_LIMITS.get(plan_id, RATE_LIMITS["free"])

    # Get remaining job quota
    jobs_remaining = get_job_creation_remaining(user_id, plan_id)

    return RateLimitStatusResponse(
        plan=plan_id,
        requests_per_minute=limits["requests_per_minute"],
        jobs_per_hour=limits["jobs_per_hour"],
        jobs_remaining_this_hour=jobs_remaining,
        rate_limiting_enabled=is_rate_limiting_enabled(),
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
@limiter.limit("5/minute")  # Additional limit on job creation
async def create_job(
    request: JobCreateRequest,
    http_request: Request,
    user_id: str = Depends(get_current_user)
) -> JobResponse:
    """
    Create a new audiobook generation job

    Requires authentication. The job will be queued for processing.
    Rate limited: 5 jobs per minute, with additional hourly limits by plan.
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

    # Validate TTS provider
    if request.tts_provider not in ["openai", "google", "gemini"]:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"TTS provider '{request.tts_provider}' is not yet implemented. "
                   f"Currently supported: 'openai', 'google', 'gemini'. ElevenLabs and Inworld coming soon."
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
        # Multilingual TTS options (Gemini TTS)
        "input_language_code": request.input_language_code,
        "output_language_code": request.output_language_code,
        "voice_preset_id": request.voice_preset_id,
        "emotion_style_prompt": request.emotion_style_prompt,
        # Findaway-specific fields
        "narrator_name": request.narrator_name,
        "genre": request.genre,
        "language": request.language,
        "isbn": request.isbn,
        "publisher": request.publisher,
        "sample_style": request.sample_style,
    }

    job = db.create_job(job_data)

    # Increment usage counter (for non-admin users)
    if not is_admin:
        try:
            db.increment_user_usage(user_id, projects=1, minutes=0)
        except Exception as e:
            # Log but don't fail - usage tracking shouldn't block job creation
            logger.warning(f"Failed to increment usage for user {user_id}: {e}")

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
    # Multilingual TTS options (Gemini TTS)
    input_language_code: str = Form(default="en-US", description="Input language code"),
    output_language_code: Optional[str] = Form(default=None, description="Output language code for translation"),
    voice_preset_id: Optional[str] = Form(default=None, description="Gemini voice preset ID"),
    emotion_style_prompt: Optional[str] = Form(default=None, description="Emotion/style prompt for TTS"),
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
    if tts_provider not in ["openai", "google", "gemini"]:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"TTS provider '{tts_provider}' is not yet implemented. Currently supported: 'openai', 'google', 'gemini'."
        )

    # Validate file type
    allowed_extensions = ['.txt', '.docx', '.pdf', '.md', '.html', '.htm', '.epub']
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
        # Multilingual TTS options (Gemini TTS)
        "input_language_code": input_language_code,
        "output_language_code": output_language_code,
        "voice_preset_id": voice_preset_id,
        "emotion_style_prompt": emotion_style_prompt,
    }

    job = db.create_job(job_data)

    # Increment usage counter
    if not is_admin:
        try:
            db.increment_user_usage(user_id, projects=1, minutes=0)
        except Exception as e:
            logger.warning(f"Failed to increment usage for user {user_id}: {e}")

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

    # Check retry limit (allow more manual retries than auto-retries)
    MAX_MANUAL_RETRIES = 10
    current_retry_count = job.get("retry_count", 0)

    if current_retry_count >= MAX_MANUAL_RETRIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum retry limit ({MAX_MANUAL_RETRIES}) reached. Please create a new job."
        )

    # Reset job for retry
    updates = {
        "status": "pending",
        "error_message": None,
        "progress_percent": 0.0,
        "current_step": "Manual retry requested",
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

    # Only allow cancelling jobs that aren't already completed or cancelled
    if job["status"] in ["completed", "cancelled"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel a job that is already {job['status']}"
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
        logger.warning(f"Failed to delete manuscript for job {job_id}: {e}")

    try:
        if job["audio_path"]:
            db.delete_storage_file("audiobooks", job["audio_path"])
    except Exception as e:
        logger.warning(f"Failed to delete audiobook for job {job_id}: {e}")

    # Delete job from database (CASCADE deletes job_files)
    db.delete_job(job_id)

    return None


# ============================================================================
# CHAPTER MANAGEMENT ENDPOINTS
# ============================================================================

class ChapterResponse(BaseModel):
    """Chapter details response"""
    id: str
    job_id: str
    chapter_index: int
    source_order: int
    title: str
    text_content: Optional[str] = None
    character_count: int = 0
    word_count: int = 0
    estimated_duration_seconds: int = 0
    status: str = "pending_review"
    segment_type: str = "body_chapter"
    audio_path: Optional[str] = None
    audio_duration_seconds: Optional[int] = None
    error_message: Optional[str] = None
    created_at: str
    updated_at: str


class ChapterUpdateRequest(BaseModel):
    """Request to update a chapter"""
    title: Optional[str] = None
    status: Optional[str] = None
    segment_type: Optional[str] = None


class ChapterReorderRequest(BaseModel):
    """Request to reorder chapters"""
    new_order: List[int]  # List of source_order values in new order


class ApproveChaptersRequest(BaseModel):
    """Request to approve chapters for TTS processing"""
    chapter_ids: Optional[List[str]] = None  # If None, approve all


@app.get(
    "/jobs/{job_id}/chapters",
    response_model=List[ChapterResponse],
    summary="Get Job Chapters",
    tags=["Chapters"],
)
async def get_job_chapters(
    job_id: str,
    user_id: str = Depends(get_current_user),
) -> List[ChapterResponse]:
    """
    Get all chapters for a job, ordered by chapter_index.

    Chapters are available after manuscript parsing (status: chapters_pending).
    """
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )

    if job["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this job"
        )

    # Get chapters from database
    try:
        chapters = db.client.table("chapters").select("*").eq(
            "job_id", job_id
        ).order("chapter_index").execute()

        return [ChapterResponse(**ch) for ch in (chapters.data or [])]
    except Exception as e:
        logger.error(f"Failed to get chapters for job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get chapters: {str(e)}"
        )


@app.get(
    "/jobs/{job_id}/chapters/{chapter_id}",
    response_model=ChapterResponse,
    summary="Get Chapter Details",
    tags=["Chapters"],
)
async def get_chapter(
    job_id: str,
    chapter_id: str,
    user_id: str = Depends(get_current_user),
) -> ChapterResponse:
    """Get details for a specific chapter."""
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )

    if job["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this job"
        )

    try:
        result = db.client.table("chapters").select("*").eq(
            "id", chapter_id
        ).eq("job_id", job_id).single().execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chapter {chapter_id} not found"
            )

        return ChapterResponse(**result.data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get chapter {chapter_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get chapter: {str(e)}"
        )


@app.patch(
    "/jobs/{job_id}/chapters/{chapter_id}",
    response_model=ChapterResponse,
    summary="Update Chapter",
    tags=["Chapters"],
)
async def update_chapter(
    job_id: str,
    chapter_id: str,
    request: ChapterUpdateRequest,
    user_id: str = Depends(get_current_user),
) -> ChapterResponse:
    """
    Update a chapter's title, status, or segment type.

    Valid statuses: pending_review, approved, excluded
    Valid segment types: front_matter, body_chapter, back_matter
    """
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )

    if job["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this job"
        )

    # Validate status
    if request.status and request.status not in [
        "pending_review", "approved", "excluded"
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status. Must be: pending_review, approved, or excluded"
        )

    # Validate segment_type
    if request.segment_type and request.segment_type not in [
        "front_matter", "body_chapter", "back_matter"
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid segment_type. Must be: front_matter, body_chapter, or back_matter"
        )

    # Build update
    updates = {}
    if request.title is not None:
        updates["title"] = request.title
    if request.status is not None:
        updates["status"] = request.status
        if request.status == "approved":
            updates["approved_at"] = datetime.utcnow().isoformat()
    if request.segment_type is not None:
        updates["segment_type"] = request.segment_type

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid updates provided"
        )

    try:
        result = db.client.table("chapters").update(updates).eq(
            "id", chapter_id
        ).eq("job_id", job_id).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chapter {chapter_id} not found"
            )

        return ChapterResponse(**result.data[0])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update chapter {chapter_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update chapter: {str(e)}"
        )


@app.post(
    "/jobs/{job_id}/chapters/reorder",
    response_model=List[ChapterResponse],
    summary="Reorder Chapters",
    tags=["Chapters"],
)
async def reorder_chapters(
    job_id: str,
    request: ChapterReorderRequest,
    user_id: str = Depends(get_current_user),
) -> List[ChapterResponse]:
    """
    Reorder chapters by providing the new order of source_order values.

    Example: If you have 3 chapters with source_order [0, 1, 2] and you want
    to move chapter 2 to the front, send new_order: [2, 0, 1]

    This updates the chapter_index for each chapter to match the new order.
    The source_order (original manuscript position) is preserved.
    """
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )

    if job["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this job"
        )

    # Only allow reordering in chapters_pending status
    if job["status"] not in ["chapters_pending", "failed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reorder chapters when job status is '{job['status']}'. "
                   f"Job must be in 'chapters_pending' status."
        )

    try:
        # Get current chapters
        chapters_result = db.client.table("chapters").select("*").eq(
            "job_id", job_id
        ).execute()
        chapters = chapters_result.data or []

        if not chapters:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No chapters found for this job"
            )

        # Validate new_order contains all source_order values
        current_source_orders = {ch["source_order"] for ch in chapters}
        new_order_set = set(request.new_order)

        if current_source_orders != new_order_set:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"new_order must contain exactly these source_order values: {sorted(current_source_orders)}"
            )

        # Update chapter_index for each chapter
        updated_chapters = []
        for new_idx, source_order in enumerate(request.new_order):
            # Find the chapter with this source_order
            chapter = next(ch for ch in chapters if ch["source_order"] == source_order)

            # Update chapter_index
            result = db.client.table("chapters").update({
                "chapter_index": new_idx
            }).eq("id", chapter["id"]).execute()

            if result.data:
                updated_chapters.append(result.data[0])

        # Return updated chapters in new order
        updated_chapters.sort(key=lambda x: x["chapter_index"])
        return [ChapterResponse(**ch) for ch in updated_chapters]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reorder chapters for job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reorder chapters: {str(e)}"
        )


@app.post(
    "/jobs/{job_id}/chapters/approve",
    response_model=JobResponse,
    summary="Approve Chapters for TTS",
    tags=["Chapters"],
)
async def approve_chapters(
    job_id: str,
    request: Optional[ApproveChaptersRequest] = None,
    user_id: str = Depends(get_current_user),
) -> JobResponse:
    """
    Approve chapters and start TTS processing.

    If chapter_ids is provided, only those chapters are approved.
    If chapter_ids is None/empty, all non-excluded chapters are approved.

    This transitions the job from 'chapters_pending' to 'processing'.
    """
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )

    if job["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this job"
        )

    # Only allow approving in chapters_pending status
    if job["status"] != "chapters_pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve chapters when job status is '{job['status']}'. "
                   f"Job must be in 'chapters_pending' status."
        )

    try:
        approved_at = datetime.utcnow().isoformat()

        if request and request.chapter_ids:
            # Approve specific chapters
            for chapter_id in request.chapter_ids:
                db.client.table("chapters").update({
                    "status": "approved",
                    "approved_at": approved_at,
                }).eq("id", chapter_id).eq("job_id", job_id).execute()
        else:
            # Approve all non-excluded chapters
            db.client.table("chapters").update({
                "status": "approved",
                "approved_at": approved_at,
            }).eq("job_id", job_id).neq("status", "excluded").execute()

        # Update job status to chapters_approved
        updated_job = db.update_job(job_id, {
            "status": "chapters_approved",
            "chapters_approved_at": approved_at,
        })

        # Enqueue job for TTS processing
        await enqueue_job(job_id)

        logger.info(f"[JOB] {job_id} - Chapters approved, queued for TTS processing")

        return JobResponse(**updated_job)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to approve chapters for job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve chapters: {str(e)}"
        )


# ============================================================================
# RETAIL SAMPLE ENDPOINTS
# ============================================================================

class RetailSampleResponse(BaseModel):
    """Retail sample response"""
    id: str
    job_id: str
    source_chapter_id: Optional[str] = None
    source_chapter_title: Optional[str] = None
    sample_text: str
    user_edited_text: Optional[str] = None
    word_count: int = 0
    character_count: int = 0
    estimated_duration_seconds: int = 0
    engagement_score: Optional[float] = None
    emotional_intensity_score: Optional[float] = None
    spoiler_risk_score: Optional[float] = None
    overall_score: Optional[float] = None
    is_auto_suggested: bool = True
    is_user_confirmed: bool = False
    is_final: bool = False
    audio_path: Optional[str] = None
    candidate_rank: Optional[int] = None
    created_at: str


class RetailSampleConfirmRequest(BaseModel):
    """Request to confirm/select a retail sample"""
    sample_id: str


@app.get(
    "/jobs/{job_id}/retail-samples",
    response_model=List[RetailSampleResponse],
    summary="Get Retail Sample Candidates",
    tags=["Retail Samples"],
)
async def get_retail_samples(
    job_id: str,
    user_id: str = Depends(get_current_user),
) -> List[RetailSampleResponse]:
    """
    Get retail sample candidates for a job.

    Returns AI-suggested samples ordered by overall_score (best first).
    """
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )

    if job["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this job"
        )

    try:
        result = db.client.table("retail_samples").select("*").eq(
            "job_id", job_id
        ).order("overall_score", desc=True).execute()

        return [RetailSampleResponse(**s) for s in (result.data or [])]
    except Exception as e:
        logger.error(f"Failed to get retail samples for job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get retail samples: {str(e)}"
        )


@app.post(
    "/jobs/{job_id}/retail-samples/confirm",
    response_model=RetailSampleResponse,
    summary="Confirm Retail Sample Selection",
    tags=["Retail Samples"],
)
async def confirm_retail_sample(
    job_id: str,
    request: RetailSampleConfirmRequest,
    user_id: str = Depends(get_current_user),
) -> RetailSampleResponse:
    """
    Confirm a retail sample selection.

    This marks the selected sample as user_confirmed and is_final.
    Only one sample can be final per job.
    """
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )

    if job["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this job"
        )

    try:
        # First, unset is_final on any existing final samples
        db.client.table("retail_samples").update({
            "is_final": False
        }).eq("job_id", job_id).eq("is_final", True).execute()

        # Set the selected sample as confirmed and final
        result = db.client.table("retail_samples").update({
            "is_user_confirmed": True,
            "is_final": True,
            "confirmed_at": datetime.utcnow().isoformat(),
        }).eq("id", request.sample_id).eq("job_id", job_id).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Retail sample {request.sample_id} not found"
            )

        # Update job to indicate retail sample is confirmed
        db.update_job(job_id, {"retail_sample_confirmed": True})

        return RetailSampleResponse(**result.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to confirm retail sample: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to confirm retail sample: {str(e)}"
        )


class RetailSampleUpdateRequest(BaseModel):
    """Request to update a retail sample's edited text"""
    user_edited_text: Optional[str] = None


@app.patch(
    "/jobs/{job_id}/retail-samples/{sample_id}",
    response_model=RetailSampleResponse,
    summary="Update Retail Sample",
    tags=["Retail Samples"],
)
async def update_retail_sample(
    job_id: str,
    sample_id: str,
    request: RetailSampleUpdateRequest,
    user_id: str = Depends(get_current_user),
) -> RetailSampleResponse:
    """
    Update a retail sample's user-edited text.

    Allows users to edit the AI-suggested sample text before confirming.
    """
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )

    if job["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this job"
        )

    try:
        # Build update data
        update_data = {}
        if request.user_edited_text is not None:
            update_data["user_edited_text"] = request.user_edited_text
            # Recalculate word count and duration based on edited text
            word_count = len(request.user_edited_text.split())
            update_data["word_count"] = word_count
            update_data["estimated_duration_seconds"] = int(word_count / 150 * 60)

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No update data provided"
            )

        result = db.client.table("retail_samples").update(
            update_data
        ).eq("id", sample_id).eq("job_id", job_id).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Retail sample {sample_id} not found"
            )

        return RetailSampleResponse(**result.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update retail sample: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update retail sample: {str(e)}"
        )


@app.post(
    "/jobs/{job_id}/retail-samples/regenerate",
    response_model=List[RetailSampleResponse],
    summary="Regenerate Retail Sample Candidates",
    tags=["Retail Samples"],
)
async def regenerate_retail_samples(
    job_id: str,
    user_id: str = Depends(get_current_user),
) -> List[RetailSampleResponse]:
    """
    Regenerate retail sample candidates for a job.

    Clears existing non-final samples and uses AI to suggest new ones.
    """
    from agents import select_retail_sample_excerpt

    job = db.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )

    if job["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this job"
        )

    # Check if there's already a confirmed final sample
    if job.get("retail_sample_confirmed"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot regenerate samples after one has been confirmed"
        )

    try:
        # Get chapters for this job to build manuscript structure
        chapters_result = db.client.table("chapters").select("*").eq(
            "job_id", job_id
        ).order("source_order").execute()

        chapters = chapters_result.data or []
        if not chapters:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No chapters found for this job. Parse manuscript first."
            )

        # Build manuscript structure for the agent
        manuscript_structure = {
            "title": job.get("title", "Untitled"),
            "author": job.get("author"),
            "chapters": [
                {
                    "index": c.get("source_order", i + 1),
                    "title": c.get("title", f"Chapter {i + 1}"),
                    "text": c.get("text_content", ""),
                }
                for i, c in enumerate(chapters)
            ]
        }

        # Get OpenAI API key
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OpenAI API key not configured"
            )

        # Delete existing non-final samples
        db.client.table("retail_samples").delete().eq(
            "job_id", job_id
        ).eq("is_final", False).execute()

        # Generate new samples using the agent
        # Generate 3 candidates with different styles
        new_samples = []
        styles = ["default", "spicy", "ultra_spicy"]

        for i, style in enumerate(styles):
            try:
                result = select_retail_sample_excerpt(
                    manuscript_structure=manuscript_structure,
                    api_key=openai_api_key,
                    target_duration_minutes=4.0,
                    preferred_style=style,
                    genre=job.get("genre"),
                )

                # Find the source chapter
                source_chapter = None
                for c in chapters:
                    if c.get("source_order") == result.get("chapter_index"):
                        source_chapter = c
                        break

                # Calculate scores (simple heuristics for now)
                word_count = result.get("approx_word_count", 0)
                # Engagement: prefer samples in the 500-800 word sweet spot
                engagement = 1.0 - abs(word_count - 650) / 650
                engagement = max(0.5, min(1.0, engagement))

                # Create sample record
                sample_data = {
                    "job_id": job_id,
                    "source_chapter_id": source_chapter["id"] if source_chapter else None,
                    "sample_text": result.get("excerpt_text", ""),
                    "word_count": word_count,
                    "estimated_duration_seconds": result.get("approx_duration_seconds", 0),
                    "engagement_score": round(engagement, 2),
                    "emotional_intensity_score": round(0.7 + (i * 0.1), 2),  # Vary by style
                    "spoiler_risk_score": round(0.2, 2),  # Early chapters = low spoiler
                    "overall_score": round((engagement + 0.7 + (i * 0.1) + (1 - 0.2)) / 3, 2),
                    "is_auto_suggested": True,
                    "is_user_confirmed": False,
                    "is_final": False,
                    "candidate_rank": i + 1,
                }

                insert_result = db.client.table("retail_samples").insert(
                    sample_data
                ).execute()

                if insert_result.data:
                    new_samples.append(insert_result.data[0])

            except Exception as e:
                logger.warning(f"Failed to generate sample with style {style}: {e}")
                continue

        if not new_samples:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate any retail sample candidates"
            )

        # Sort by overall score
        new_samples.sort(key=lambda x: x.get("overall_score", 0), reverse=True)

        return [RetailSampleResponse(**s) for s in new_samples]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to regenerate retail samples: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate retail samples: {str(e)}"
        )


# ============================================================================
# TRACKS/DOWNLOADS ENDPOINTS
# ============================================================================

class TrackResponse(BaseModel):
    """Audio track response"""
    id: str
    job_id: str
    chapter_id: Optional[str] = None
    track_index: int
    title: str
    segment_type: str
    audio_path: Optional[str] = None
    duration_seconds: Optional[int] = None
    file_size_bytes: Optional[int] = None
    export_filename: Optional[str] = None
    status: str = "pending"
    created_at: str


class TrackDownloadUrlResponse(BaseModel):
    """Track download URL response"""
    track_id: str
    export_filename: str
    download_url: str
    expires_in: int = 3600


@app.get(
    "/jobs/{job_id}/tracks",
    response_model=List[TrackResponse],
    summary="Get Job Tracks",
    tags=["Tracks"],
)
async def get_job_tracks(
    job_id: str,
    user_id: str = Depends(get_current_user),
) -> List[TrackResponse]:
    """
    Get all audio tracks for a completed job.

    Tracks are in playback order with Findaway-compatible filenames.
    """
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )

    if job["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this job"
        )

    try:
        result = db.client.table("tracks").select("*").eq(
            "job_id", job_id
        ).order("track_index").execute()

        return [TrackResponse(**t) for t in (result.data or [])]
    except Exception as e:
        logger.error(f"Failed to get tracks for job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tracks: {str(e)}"
        )


@app.get(
    "/jobs/{job_id}/tracks/{track_id}/download",
    response_model=TrackDownloadUrlResponse,
    summary="Get Track Download URL",
    tags=["Tracks"],
)
async def get_track_download_url(
    job_id: str,
    track_id: str,
    user_id: str = Depends(get_current_user),
) -> TrackDownloadUrlResponse:
    """
    Get presigned download URL for a specific track.

    The URL expires in 1 hour.
    """
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )

    if job["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this job"
        )

    try:
        result = db.client.table("tracks").select("*").eq(
            "id", track_id
        ).eq("job_id", job_id).single().execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Track {track_id} not found"
            )

        track = result.data
        if not track.get("audio_path"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Track audio not available yet"
            )

        download_url = db.get_download_url(track["audio_path"], expires_in=3600)

        return TrackDownloadUrlResponse(
            track_id=track_id,
            export_filename=track.get("export_filename") or f"track_{track['track_index']:02d}.mp3",
            download_url=download_url,
            expires_in=3600,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get track download URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get download URL: {str(e)}"
        )


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
# TTS VOICE LIBRARY & PREVIEW ENDPOINTS
# ============================================================================

class VoicePresetResponse(BaseModel):
    """Voice preset information"""
    id: str
    label: str
    description: str
    voice_name: str
    default_language_code: str
    gender: str
    style: str
    sample_text: str = ""


class LanguageInfo(BaseModel):
    """Language information"""
    code: str
    name: str


class VoiceLibraryResponse(BaseModel):
    """Voice library with presets and supported languages"""
    voice_presets: List[VoicePresetResponse]
    input_languages: List[LanguageInfo]
    output_languages: List[LanguageInfo]


class TTSPreviewRequest(BaseModel):
    """Request to preview TTS voice"""
    text: str = "My heart found its home in your hands. Every whisper between us tells a story of forever."
    preset_id: str = "studio_neutral"
    input_language_code: str = "en-US"
    output_language_code: Optional[str] = None
    emotion_style_prompt: Optional[str] = None


class TTSPreviewResponse(BaseModel):
    """TTS preview response"""
    success: bool
    audio_url: Optional[str] = None
    audio_base64: Optional[str] = None
    preset_id: str
    input_language: str
    output_language: str
    duration_estimate_seconds: Optional[float] = None
    error: Optional[str] = None


@app.get(
    "/tts/voices",
    response_model=VoiceLibraryResponse,
    summary="Get Voice Library",
    description="Get all available voice presets and supported languages for TTS",
    tags=["TTS"],
)
async def get_voice_library() -> VoiceLibraryResponse:
    """
    Get the complete voice library including:
    - Voice presets with descriptions
    - Supported input languages
    - Supported output languages
    """
    try:
        from tts import get_voice_presets, get_supported_languages

        presets = get_voice_presets()
        languages = get_supported_languages()

        # Convert to response format
        voice_presets = [
            VoicePresetResponse(**preset) for preset in presets
        ]

        language_list = [
            LanguageInfo(code=code, name=name)
            for code, name in languages.items()
        ]

        # Input languages include "auto" for auto-detection
        input_language_list = language_list

        # Output languages should NOT include "auto" - user must choose explicitly
        output_language_list = [
            lang for lang in language_list if lang.code != "auto"
        ]

        return VoiceLibraryResponse(
            voice_presets=voice_presets,
            input_languages=input_language_list,
            output_languages=output_language_list,
        )

    except Exception as e:
        logger.error(f"Failed to get voice library: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get voice library: {str(e)}"
        )


@app.post(
    "/tts/preview",
    response_model=TTSPreviewResponse,
    summary="Preview TTS Voice",
    description="Generate a short audio preview with the selected voice and settings",
    tags=["TTS"],
)
async def preview_tts(
    request: TTSPreviewRequest,
    user_id: str = Depends(get_current_user),
) -> TTSPreviewResponse:
    """
    Generate a TTS preview with the selected voice preset and emotion settings.

    This endpoint:
    1. Takes a short text snippet (limited to 500 characters)
    2. Generates audio using Gemini TTS
    3. Returns base64-encoded audio for immediate playback
    """
    try:
        # Limit text length for preview
        preview_text = request.text[:500]

        # Log the request parameters for debugging
        logger.info(f"[TTS Preview] Request received:")
        logger.info(f"[TTS Preview]   - preset_id: {request.preset_id}")
        logger.info(f"[TTS Preview]   - input_language_code: {request.input_language_code}")
        logger.info(f"[TTS Preview]   - output_language_code: {request.output_language_code}")
        logger.info(f"[TTS Preview]   - emotion_style_prompt: {request.emotion_style_prompt}")
        logger.info(f"[TTS Preview]   - text preview: {preview_text[:100]}...")

        from tts import synthesize_segment

        # IMPORTANT: Pass output_language_code as-is (None if not specified)
        # DO NOT fallback to input_language_code here - that breaks translation!
        # synthesize_segment will handle the fallback logic correctly
        audio_bytes = await synthesize_segment(
            text=preview_text,
            preset_id=request.preset_id,
            input_language_code=request.input_language_code,
            output_language_code=request.output_language_code,  # Pass as-is, no fallback!
            emotion_style_prompt=request.emotion_style_prompt,
        )

        # Encode as base64 for frontend playback
        import base64
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

        # Estimate duration (rough: ~150 words/minute, ~5 chars/word)
        word_count = len(preview_text.split())
        duration_estimate = word_count / 150 * 60  # seconds

        # Determine the actual output language for the response
        actual_output_lang = request.output_language_code or request.input_language_code
        logger.info(f"TTS preview generated for user {user_id}: {len(audio_bytes)} bytes")
        logger.info(f"[TTS Preview]   - Actual output language: {actual_output_lang}")

        return TTSPreviewResponse(
            success=True,
            audio_base64=audio_base64,
            preset_id=request.preset_id,
            input_language=request.input_language_code,
            output_language=actual_output_lang,
            duration_estimate_seconds=round(duration_estimate, 1),
        )

    except Exception as e:
        logger.error(f"TTS preview failed: {e}")
        return TTSPreviewResponse(
            success=False,
            preset_id=request.preset_id,
            input_language=request.input_language_code,
            output_language=request.output_language_code or request.input_language_code,
            error=str(e),
        )


# ============================================================================
# GOOGLE DRIVE INTEGRATION ENDPOINTS
# ============================================================================

class GoogleDriveAuthUrlResponse(BaseModel):
    """Google Drive OAuth URL response"""
    auth_url: str
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
        oauth_url = get_oauth_url(state=state)
        return GoogleDriveAuthUrlResponse(auth_url=oauth_url, state=state)
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
        logger.error(f"Google Drive OAuth error: {e}")
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
        logger.error(f"Error fetching job stats: {e}")
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
        logger.error(f"Error fetching user stats: {e}")
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
        logger.error(f"Error fetching recent errors: {e}")
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
# MULTILINGUAL TTS SMOKE TEST
# ============================================================================

class MultilingualTestRequest(BaseModel):
    """Request for multilingual TTS smoke test"""
    text: str = "My heart found its home in your hands."
    input_language_code: str = "en-US"
    output_language_code: str = "mr-IN"  # Marathi
    voice_preset_id: str = "romantic_female"
    emotion_style_prompt: Optional[str] = "soft, romantic, intimate"


class MultilingualTestResponse(BaseModel):
    """Response from multilingual TTS smoke test"""
    success: bool
    job_id: Optional[str] = None
    input_language: str
    output_language: str
    voice_preset: str
    translated_text: Optional[str] = None
    audio_r2_url: Optional[str] = None
    audio_size_bytes: Optional[int] = None
    duration_estimate_seconds: Optional[float] = None
    error: Optional[str] = None
    details: Dict[str, Any] = {}


@app.post(
    "/debug/multilingual-test",
    response_model=MultilingualTestResponse,
    tags=["Debug"],
    summary="Run multilingual TTS smoke test",
    description="""
    Debug endpoint to test the full multilingual TTS pipeline.
    Requires: GOOGLE_GENAI_API_KEY

    This endpoint:
    1. Takes a short English text
    2. Translates it to the target language (default: Marathi)
    3. Generates audio using Gemini TTS with specified voice preset
    4. Uploads to R2 storage
    5. Returns the R2 URL for playback
    """,
)
async def run_multilingual_test(
    request: MultilingualTestRequest,
    user_id: str = Depends(get_current_user),
) -> MultilingualTestResponse:
    """
    Run a multilingual TTS smoke test.
    """
    import uuid
    import tempfile
    from pathlib import Path

    # Check if user is admin
    admin_emails_str = os.getenv("ADMIN_EMAILS", "")
    admin_emails = [e.strip().lower() for e in admin_emails_str.split(",") if e.strip()]

    # Get user email
    user_data = db.get_user(user_id)
    user_email = user_data.get("email", "").lower() if user_data else ""

    if user_email not in admin_emails:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Multilingual test endpoint is only available to admin users."
        )

    # Initialize response
    test_id = f"mltest-{uuid.uuid4().hex[:8]}"
    response = MultilingualTestResponse(
        success=False,
        job_id=test_id,
        input_language=request.input_language_code,
        output_language=request.output_language_code,
        voice_preset=request.voice_preset_id,
    )

    try:
        # Import TTS modules
        from tts import synthesize_segment, translate_text

        # Step 1: Translate if needed
        translated_text = request.text
        if request.input_language_code != request.output_language_code:
            logger.info(f"[ML-TEST] Translating from {request.input_language_code} to {request.output_language_code}")
            translated_text = await translate_text(
                text=request.text,
                source_lang=request.input_language_code,
                target_lang=request.output_language_code,
            )
            response.translated_text = translated_text
            response.details["original_text"] = request.text
            logger.info(f"[ML-TEST] Translation complete: {translated_text[:100]}...")

        # Step 2: Generate TTS audio
        logger.info(f"[ML-TEST] Generating TTS with preset: {request.voice_preset_id}")
        audio_bytes = await synthesize_segment(
            text=translated_text,
            preset_id=request.voice_preset_id,
            input_language_code=request.output_language_code,  # Already translated
            output_language_code=request.output_language_code,
            emotion_style_prompt=request.emotion_style_prompt,
        )

        response.audio_size_bytes = len(audio_bytes)
        logger.info(f"[ML-TEST] Generated {len(audio_bytes)} bytes of audio")

        # Step 3: Upload to R2
        storage_path = db.upload_audiobook(
            user_id=user_id,
            job_id=test_id,
            filename=f"multilingual_test_{request.output_language_code}.mp3",
            file_content=audio_bytes,
        )

        # Step 4: Get presigned URL
        audio_url = db.get_download_url(storage_path, expires_in=3600)  # 1 hour
        response.audio_r2_url = audio_url
        response.details["storage_path"] = storage_path

        # Estimate duration
        word_count = len(translated_text.split())
        response.duration_estimate_seconds = round(word_count / 150 * 60, 1)

        response.success = True
        logger.info(f"[ML-TEST] Success! Audio available at: {audio_url[:50]}...")

    except ImportError as e:
        response.error = f"Import error: {str(e)}. Make sure google-genai is installed."
        response.details["import_error"] = str(e)
        logger.error(f"[ML-TEST] Import error: {e}")

    except Exception as e:
        import traceback
        response.error = f"{type(e).__name__}: {str(e)}"
        response.details["traceback"] = traceback.format_exc()
        logger.error(f"[ML-TEST] Error: {e}")

    return response


# ============================================================================
# ANALYTICS DASHBOARD
# ============================================================================

class AnalyticsTimeRange(str, Enum):
    """Time range for analytics queries."""
    day = "day"
    week = "week"
    month = "month"
    year = "year"
    all_time = "all_time"


class AnalyticsResponse(BaseModel):
    """Analytics dashboard response."""
    time_range: str

    # Usage Statistics
    total_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    pending_jobs: int = 0
    success_rate: float = 0.0

    # Audio Statistics
    total_audio_minutes: float = 0.0
    total_words_processed: int = 0
    avg_audio_duration_minutes: float = 0.0

    # Processing Statistics
    avg_processing_time_seconds: float = 0.0
    min_processing_time_seconds: float = 0.0
    max_processing_time_seconds: float = 0.0

    # Popular Voices
    popular_voices: List[Dict[str, Any]] = []

    # Language Statistics
    popular_input_languages: List[Dict[str, Any]] = []
    popular_output_languages: List[Dict[str, Any]] = []

    # Error Statistics
    error_rate: float = 0.0
    common_errors: List[Dict[str, Any]] = []

    # Trends (for charts)
    jobs_by_day: List[Dict[str, Any]] = []
    jobs_by_status: Dict[str, int] = {}

    # User Statistics (admin only)
    unique_users: int = 0
    new_users_in_period: int = 0


@app.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    time_range: AnalyticsTimeRange = AnalyticsTimeRange.month,
    user_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """
    Get analytics dashboard data.

    - Regular users can only see their own analytics (user_id is ignored)
    - Admins can see all analytics or filter by user_id
    """
    db = SupabaseClient()

    # Determine if user is admin
    is_admin = False
    try:
        profile = db.client.table("profiles").select("subscription_plan").eq("id", current_user["id"]).single().execute()
        is_admin = profile.data.get("subscription_plan") == "admin" if profile.data else False
    except Exception:
        pass

    # Non-admins can only see their own data
    if not is_admin:
        user_id = current_user["id"]

    # Calculate date range
    from datetime import datetime, timedelta
    now = datetime.utcnow()

    if time_range == AnalyticsTimeRange.day:
        start_date = now - timedelta(days=1)
    elif time_range == AnalyticsTimeRange.week:
        start_date = now - timedelta(weeks=1)
    elif time_range == AnalyticsTimeRange.month:
        start_date = now - timedelta(days=30)
    elif time_range == AnalyticsTimeRange.year:
        start_date = now - timedelta(days=365)
    else:  # all_time
        start_date = datetime(2020, 1, 1)  # Far enough back

    start_date_str = start_date.isoformat()

    try:
        # Build query
        query = db.client.table("jobs").select("*")

        if user_id:
            query = query.eq("user_id", user_id)

        query = query.gte("created_at", start_date_str)

        result = query.execute()
        jobs = result.data or []

        # Calculate statistics
        total_jobs = len(jobs)
        completed_jobs = len([j for j in jobs if j.get("status") == "completed"])
        failed_jobs = len([j for j in jobs if j.get("status") == "failed"])
        pending_jobs = len([j for j in jobs if j.get("status") in ["pending", "processing", "parsing", "chapters_pending", "chapters_approved"]])

        success_rate = (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0.0
        error_rate = (failed_jobs / total_jobs * 100) if total_jobs > 0 else 0.0

        # Audio statistics
        total_audio_seconds = sum(j.get("duration_seconds") or 0 for j in jobs if j.get("status") == "completed")
        total_audio_minutes = total_audio_seconds / 60

        total_words = sum(j.get("word_count") or 0 for j in jobs)

        avg_audio_minutes = (total_audio_minutes / completed_jobs) if completed_jobs > 0 else 0.0

        # Processing time statistics
        processing_times = []
        for job in jobs:
            if job.get("status") == "completed" and job.get("created_at") and job.get("completed_at"):
                try:
                    created = datetime.fromisoformat(job["created_at"].replace("Z", "+00:00"))
                    completed = datetime.fromisoformat(job["completed_at"].replace("Z", "+00:00"))
                    processing_times.append((completed - created).total_seconds())
                except Exception:
                    pass

        avg_processing = sum(processing_times) / len(processing_times) if processing_times else 0.0
        min_processing = min(processing_times) if processing_times else 0.0
        max_processing = max(processing_times) if processing_times else 0.0

        # Popular voices
        voice_counts = {}
        for job in jobs:
            voice = job.get("voice_preset_id") or job.get("voice_id") or "default"
            voice_counts[voice] = voice_counts.get(voice, 0) + 1

        popular_voices = [
            {"voice_id": v, "count": c, "percentage": round(c / total_jobs * 100, 1) if total_jobs > 0 else 0}
            for v, c in sorted(voice_counts.items(), key=lambda x: -x[1])[:10]
        ]

        # Language statistics
        input_lang_counts = {}
        output_lang_counts = {}
        for job in jobs:
            input_lang = job.get("input_language_code") or "en"
            output_lang = job.get("output_language_code") or "en"
            input_lang_counts[input_lang] = input_lang_counts.get(input_lang, 0) + 1
            output_lang_counts[output_lang] = output_lang_counts.get(output_lang, 0) + 1

        popular_input_languages = [
            {"language": lang, "count": c, "percentage": round(c / total_jobs * 100, 1) if total_jobs > 0 else 0}
            for lang, c in sorted(input_lang_counts.items(), key=lambda x: -x[1])[:5]
        ]

        popular_output_languages = [
            {"language": lang, "count": c, "percentage": round(c / total_jobs * 100, 1) if total_jobs > 0 else 0}
            for lang, c in sorted(output_lang_counts.items(), key=lambda x: -x[1])[:5]
        ]

        # Common errors
        error_counts = {}
        for job in jobs:
            if job.get("status") == "failed" and job.get("error_message"):
                error_msg = job["error_message"][:100]  # Truncate
                error_counts[error_msg] = error_counts.get(error_msg, 0) + 1

        common_errors = [
            {"error": e, "count": c}
            for e, c in sorted(error_counts.items(), key=lambda x: -x[1])[:5]
        ]

        # Jobs by day (for charts)
        jobs_by_day_dict = {}
        for job in jobs:
            if job.get("created_at"):
                try:
                    day = job["created_at"][:10]  # YYYY-MM-DD
                    jobs_by_day_dict[day] = jobs_by_day_dict.get(day, 0) + 1
                except Exception:
                    pass

        jobs_by_day = [
            {"date": d, "count": c}
            for d, c in sorted(jobs_by_day_dict.items())[-30:]  # Last 30 days
        ]

        # Jobs by status
        jobs_by_status = {
            "completed": completed_jobs,
            "failed": failed_jobs,
            "pending": pending_jobs,
        }

        # User statistics (admin only)
        unique_users = 0
        new_users_in_period = 0
        if is_admin:
            unique_user_ids = set(j.get("user_id") for j in jobs if j.get("user_id"))
            unique_users = len(unique_user_ids)

            # New users (users whose first job is in this period)
            try:
                all_users_result = db.client.table("profiles").select("id, created_at").execute()
                if all_users_result.data:
                    new_users_in_period = len([
                        u for u in all_users_result.data
                        if u.get("created_at") and u["created_at"] >= start_date_str
                    ])
            except Exception:
                pass

        return AnalyticsResponse(
            time_range=time_range.value,
            total_jobs=total_jobs,
            completed_jobs=completed_jobs,
            failed_jobs=failed_jobs,
            pending_jobs=pending_jobs,
            success_rate=round(success_rate, 1),
            total_audio_minutes=round(total_audio_minutes, 1),
            total_words_processed=total_words,
            avg_audio_duration_minutes=round(avg_audio_minutes, 1),
            avg_processing_time_seconds=round(avg_processing, 1),
            min_processing_time_seconds=round(min_processing, 1),
            max_processing_time_seconds=round(max_processing, 1),
            popular_voices=popular_voices,
            popular_input_languages=popular_input_languages,
            popular_output_languages=popular_output_languages,
            error_rate=round(error_rate, 1),
            common_errors=common_errors,
            jobs_by_day=jobs_by_day,
            jobs_by_status=jobs_by_status,
            unique_users=unique_users,
            new_users_in_period=new_users_in_period,
        )

    except Exception as e:
        logger.error(f"Analytics error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch analytics: {str(e)}")


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
