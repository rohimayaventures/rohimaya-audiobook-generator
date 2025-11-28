"""
Background Worker for Audiobook Generation
Processes jobs asynchronously using asyncio

Handles:
- Job queue management
- Pipeline execution (single-voice, dual-voice, findaway)
- Audio upload to R2
- Job status updates
- Duration calculation
- Findaway package creation (ZIP with manifest, cover, audio)
"""

import os
import sys
import json
import asyncio
import traceback
import tempfile
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Setup logging with structured format for easy searching
# Log tags: [JOB], [WORKER], [PIPELINE]
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("worker")

from .database import db

# Load environment variables (only for local development)
# In production (Railway), env vars are set directly
env_path = Path(__file__).parent.parent.parent.parent / "env" / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

# Try to import pydub for duration calculation
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    logger.warning("pydub not available - audio duration calculation disabled")

# Job queue
job_queue: asyncio.Queue = asyncio.Queue()
processing_jobs: set = set()


def get_audio_duration(audio_path: Path) -> int:
    """
    Calculate audio duration in seconds using pydub.

    Args:
        audio_path: Path to audio file

    Returns:
        Duration in seconds (0 if calculation fails)
    """
    if not PYDUB_AVAILABLE:
        logger.warning("pydub not available, returning 0 for duration")
        return 0

    try:
        audio = AudioSegment.from_file(str(audio_path))
        duration_ms = len(audio)
        duration_seconds = int(duration_ms / 1000)
        logger.info(f"Audio duration: {duration_seconds} seconds")
        return duration_seconds
    except Exception as e:
        logger.error(f"Failed to calculate duration: {e}")
        return 0


def get_temp_directory(job_id: str) -> Path:
    """
    Get cross-platform temp directory for job processing.

    Args:
        job_id: Job UUID

    Returns:
        Path to temp directory
    """
    # Use system temp directory for cross-platform compatibility
    base_temp = Path(tempfile.gettempdir())
    job_temp = base_temp / "authorflow_jobs" / job_id
    job_temp.mkdir(parents=True, exist_ok=True)
    logger.info(f"Using temp directory: {job_temp}")
    return job_temp


async def enqueue_job(job_id: str):
    """
    Add job to processing queue

    Args:
        job_id: Job UUID to process
    """
    await job_queue.put(job_id)
    logger.info(f"📥 Job {job_id} added to queue (queue size: {job_queue.qsize()})")


async def process_job(job_id: str):
    """
    Process a single audiobook job

    Args:
        job_id: Job UUID

    This function:
    1. Fetches job from database
    2. Downloads manuscript from storage
    3. Runs appropriate pipeline (single-voice or dual-voice)
    4. Uploads generated audio to storage
    5. Updates job status to completed or failed
    """
    output_dir = None

    try:
        # Add to processing set
        processing_jobs.add(job_id)

        # Fetch job from database
        job = db.get_job(job_id)
        if not job:
            logger.error(f"[JOB] {job_id} - Not found in database")
            return

        logger.info(f"[JOB] {job_id} - Starting: {job['title']}")
        logger.info(f"[JOB] {job_id} - Mode: {job['mode']}, Provider: {job['tts_provider']}, Voice: {job.get('narrator_voice_id')}")

        # Update status to processing
        db.update_job(job_id, {
            "status": "processing",
            "started_at": datetime.utcnow().isoformat(),
            "progress_percent": 5.0,
        })

        # Download manuscript from storage
        source_path = job.get("source_path")
        if not source_path:
            raise ValueError("No source_path found for job - manuscript not uploaded")

        logger.info(f"[JOB] {job_id} - Downloading manuscript from: {source_path}")
        manuscript_data = db.download_manuscript(source_path)
        manuscript_text = manuscript_data.decode("utf-8")

        word_count = len(manuscript_text.split())
        logger.info(f"[JOB] {job_id} - Manuscript downloaded: {len(manuscript_text)} chars, ~{word_count} words")

        # Update progress
        db.update_job(job_id, {"progress_percent": 10.0})

        # Determine which pipeline to use
        mode = job["mode"]
        tts_provider = job["tts_provider"]

        # Create temp directory (cross-platform)
        output_dir = get_temp_directory(job_id)

        # ======================================================================
        # DEBUG: Log pipeline parameters before execution
        # ======================================================================
        logger.info(f"[PIPELINE] {job_id} - Pipeline parameters:")
        logger.info(f"[PIPELINE] {job_id} -   mode: {mode}")
        logger.info(f"[PIPELINE] {job_id} -   tts_provider: {tts_provider}")
        logger.info(f"[PIPELINE] {job_id} -   output_dir: {output_dir}")
        logger.info(f"[PIPELINE] {job_id} -   manuscript_text length: {len(manuscript_text)} chars")

        # Import and run pipelines
        if mode == "single_voice":
            # Currently only OpenAI is supported for single-voice
            if tts_provider != "openai":
                logger.warning(f"[JOB] {job_id} - Forcing provider from {tts_provider} to openai (only supported)")
                tts_provider = "openai"

            from ..pipelines.standard_single_voice import generate_single_voice_audiobook

            # Get API key
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not configured in environment")

            # Run pipeline
            logger.info(f"[PIPELINE] {job_id} - Running single-voice pipeline")

            db.update_job(job_id, {"progress_percent": 15.0})

            audio_files = await asyncio.to_thread(
                generate_single_voice_audiobook,
                manuscript_text,
                output_dir,
                api_key,
                job["narrator_voice_id"],
                tts_provider,
                job["title"],  # Pass book title for final merged file
            )

        elif mode == "dual_voice":
            from ..pipelines.phoenix_peacock_dual_voice import generate_dual_voice_audiobook

            # Get API key (dual-voice uses ElevenLabs)
            api_key = os.getenv("ELEVENLABS_API_KEY")
            if not api_key:
                raise ValueError("ELEVENLABS_API_KEY not configured in environment")

            # Run pipeline
            logger.info(f"[PIPELINE] {job_id} - Running dual-voice pipeline")
            logger.info(f"[PIPELINE] {job_id} - Narrator: {job['narrator_voice_id']}, Character: {job['character_voice_id']} ({job['character_name']})")

            db.update_job(job_id, {"progress_percent": 15.0})

            audio_files = await asyncio.to_thread(
                generate_dual_voice_audiobook,
                manuscript_text,
                output_dir,
                api_key,
                job["narrator_voice_id"],
                job["character_voice_id"],
                job["character_name"],
            )

        elif mode == "findaway":
            # Findaway-ready package with cover, manifest, and ZIP
            from ..pipelines.findaway_pipeline import generate_findaway_audiobook

            # Get API key (Findaway uses OpenAI for TTS and cover)
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not configured in environment")

            # Build metadata from job
            book_metadata = {
                "title": job.get("title"),
                "author": job.get("author"),
                "narrator": job.get("narrator_name"),
                "genre": job.get("genre"),
                "language": job.get("language", "en"),
                "isbn": job.get("isbn"),
                "publisher": job.get("publisher", "AuthorFlow Studios"),
                "sample_style": job.get("sample_style", "default"),
                "cover_vibe": job.get("cover_vibe"),
            }

            logger.info(f"[PIPELINE] {job_id} - Running Findaway pipeline")
            logger.info(f"[PIPELINE] {job_id} - Title: {book_metadata['title']}, Author: {book_metadata['author']}")

            # Progress callback to update job status
            def progress_callback(percent: float, message: str):
                db.update_job(job_id, {
                    "progress_percent": percent,
                    "current_step": message,
                })

            # Run Findaway pipeline
            result = await asyncio.to_thread(
                generate_findaway_audiobook,
                manuscript_text,
                output_dir,
                api_key,
                job["narrator_voice_id"],
                book_metadata,
                progress_callback,
            )

            # Handle Findaway result differently - upload ZIP package
            zip_path = result.get("zip_path")
            if not zip_path or not zip_path.exists():
                raise RuntimeError("Findaway pipeline did not produce ZIP package")

            logger.info(f"[JOB] {job_id} - Uploading Findaway package: {zip_path.name}")

            # Read ZIP file
            with open(zip_path, "rb") as f:
                zip_content = f.read()

            # Upload ZIP to R2
            safe_title = "".join(c for c in job['title'] if c.isalnum() or c in (' ', '-', '_')).strip()
            if not safe_title:
                safe_title = "audiobook"

            storage_path = db.upload_audiobook(
                user_id=job["user_id"],
                job_id=job_id,
                filename=f"{safe_title}_findaway_package.zip",
                file_content=zip_content,
            )

            logger.info(f"[JOB] {job_id} - Uploaded to R2: {storage_path}")

            # Also upload individual merged audio for playback
            manifest_data = result.get("manifest", {})
            audio_files_list = result.get("audio_files", [])

            # Get duration from manifest
            duration_seconds = manifest_data.get("audio", {}).get("total_duration_seconds", 0)
            file_size = zip_path.stat().st_size

            # Update job with Findaway-specific data
            db.update_job(job_id, {
                "status": "completed",
                "audio_path": storage_path,
                "file_size_bytes": file_size,
                "duration_seconds": duration_seconds,
                "progress_percent": 100.0,
                "completed_at": datetime.utcnow().isoformat(),
                "error_message": None,
                # Findaway-specific fields
                "package_type": "findaway",
                "section_count": result.get("section_count", 0),
                "has_cover": result.get("cover_path") is not None,
                "manifest_json": json.dumps(manifest_data) if manifest_data else None,
            })

            logger.info(f"[JOB] {job_id} - Completed (Findaway) - Duration: {duration_seconds}s, Sections: {result.get('section_count', 0)}")

            # Skip the normal upload flow since we handled it above
            return

        else:
            raise ValueError(f"Unknown mode: {mode}. Supported modes: single_voice, dual_voice, findaway")

        # ======================================================================
        # DEBUG: Log pipeline output after execution
        # ======================================================================
        logger.info(f"[PIPELINE] {job_id} - Pipeline returned:")
        logger.info(f"[PIPELINE] {job_id} -   audio_files type: {type(audio_files)}")
        logger.info(f"[PIPELINE] {job_id} -   audio_files count: {len(audio_files) if audio_files else 0}")
        if audio_files:
            for i, af in enumerate(audio_files):
                af_path = Path(af)
                exists = af_path.exists() if af else False
                size = af_path.stat().st_size if exists else 0
                logger.info(f"[PIPELINE] {job_id} -   [{i}] {af} (exists={exists}, size={size})")

        # Update progress
        db.update_job(job_id, {"progress_percent": 80.0})

        # Validate pipeline output
        if not audio_files:
            raise RuntimeError(
                "Pipeline returned empty list - no audio files were generated. "
                "This may indicate the manuscript couldn't be parsed into chapters, "
                "or all TTS API calls failed."
            )

        # Get the final audio file (last item in list)
        final_audio_path = Path(audio_files[-1]) if audio_files else None

        if not final_audio_path:
            raise RuntimeError("Pipeline returned None as final audio path")

        if not final_audio_path.exists():
            # Enhanced error logging for debugging
            logger.error(f"[JOB] {job_id} - Final audio missing!")
            logger.error(f"[JOB] {job_id} -   Expected path: {final_audio_path}")
            logger.error(f"[JOB] {job_id} -   All audio_files: {[str(p) for p in audio_files]}")

            # Check what files actually exist in output_dir
            if output_dir.exists():
                existing_files = list(output_dir.glob("*"))
                logger.error(f"[JOB] {job_id} -   Files in output_dir: {[f.name for f in existing_files]}")
            else:
                logger.error(f"[JOB] {job_id} -   output_dir does not exist: {output_dir}")

            raise FileNotFoundError(
                f"Final audio file not found at: {final_audio_path}. "
                f"Generated files: {[str(f) for f in audio_files]}. "
                f"Check Railway logs for [PIPELINE] entries to see what was returned."
            )

        file_size_bytes = final_audio_path.stat().st_size
        logger.info(f"[JOB] {job_id} - Uploading final audio: {final_audio_path.name} ({file_size_bytes} bytes)")

        # Calculate duration
        duration_seconds = get_audio_duration(final_audio_path)

        # Read final audio file
        with open(final_audio_path, "rb") as f:
            audio_content = f.read()

        # Sanitize filename for storage
        safe_title = "".join(c for c in job['title'] if c.isalnum() or c in (' ', '-', '_')).strip()
        if not safe_title:
            safe_title = "audiobook"

        # Upload to R2 Storage
        storage_path = db.upload_audiobook(
            user_id=job["user_id"],
            job_id=job_id,
            filename=f"{safe_title}_COMPLETE.mp3",
            file_content=audio_content,
        )

        logger.info(f"[JOB] {job_id} - Uploaded to R2: {storage_path}")

        # Get file stats
        file_size = final_audio_path.stat().st_size

        # Update job to completed
        db.update_job(job_id, {
            "status": "completed",
            "audio_path": storage_path,
            "file_size_bytes": file_size,
            "duration_seconds": duration_seconds,
            "progress_percent": 100.0,
            "completed_at": datetime.utcnow().isoformat(),
            "error_message": None,  # Clear any previous error
        })

        logger.info(f"[JOB] {job_id} - Completed - Duration: {duration_seconds}s, Size: {file_size} bytes")

    except Exception as e:
        # Log error with full traceback
        error_message = f"{type(e).__name__}: {str(e)}"
        logger.error(f"[JOB] {job_id} - Failed: {error_message}")
        logger.error(traceback.format_exc())

        # Update job to failed with detailed error
        db.update_job(job_id, {
            "status": "failed",
            "error_message": error_message,
            "completed_at": datetime.utcnow().isoformat(),
        })

    finally:
        # Remove from processing set
        processing_jobs.discard(job_id)

        # Clean up temp files
        if output_dir and output_dir.exists():
            try:
                shutil.rmtree(output_dir)
                logger.debug(f"[JOB] {job_id} - Cleaned up temp directory")
            except Exception as e:
                logger.warning(f"[JOB] {job_id} - Failed to clean up temp directory: {e}")


async def worker_loop():
    """
    Main worker loop that processes jobs from the queue
    Run this as a background task in FastAPI
    """
    global _worker_running
    _worker_running = True

    logger.info("[WORKER] Background worker started")
    logger.info(f"[WORKER]   pydub available: {PYDUB_AVAILABLE}")
    logger.info(f"[WORKER]   Temp directory: {tempfile.gettempdir()}")

    while True:
        try:
            # Get job from queue (wait if empty)
            job_id = await job_queue.get()

            try:
                # Skip if already processing
                if job_id in processing_jobs:
                    logger.warning(f"⏭️ Job {job_id} already processing, skipping duplicate")
                    continue

                # Process job
                await process_job(job_id)

            finally:
                # Always mark task as done, even if skipped or errored
                job_queue.task_done()

        except asyncio.CancelledError:
            logger.info("[WORKER] Worker loop cancelled, shutting down...")
            _worker_running = False
            break
        except Exception as e:
            logger.error(f"❌ Worker loop error: {e}")
            logger.error(traceback.format_exc())
            await asyncio.sleep(5)  # Wait before retrying


def get_queue_status() -> Dict[str, Any]:
    """
    Get current queue status

    Returns:
        Dictionary with queue stats
    """
    return {
        "queued_jobs": job_queue.qsize(),
        "processing_jobs": len(processing_jobs),
        "processing_job_ids": list(processing_jobs),
        "total": job_queue.qsize() + len(processing_jobs),
    }


# Flag to track if worker is running
_worker_running: bool = False


def is_worker_running() -> bool:
    """Check if the background worker is running"""
    return _worker_running


async def recover_pending_jobs() -> Dict[str, Any]:
    """
    Recover jobs that were pending or processing when the server restarted.

    This function queries the database for jobs with status 'pending' or 'processing'
    and re-enqueues them for processing.

    Jobs in 'processing' state are treated as interrupted (server crashed mid-processing)
    and are reset to 'pending' before re-enqueueing.

    Returns:
        Dictionary with recovery statistics
    """
    logger.info("[WORKER] Starting job recovery scan...")

    recovered_pending = 0
    recovered_processing = 0
    recovered_job_ids = []
    errors = []

    try:
        # Query for pending jobs
        pending_jobs = db.client.table("jobs").select("id, title, status").eq(
            "status", "pending"
        ).execute()

        if pending_jobs.data:
            for job in pending_jobs.data:
                try:
                    await enqueue_job(job["id"])
                    recovered_pending += 1
                    recovered_job_ids.append(job["id"])
                    logger.info(f"[WORKER] Recovered pending job: {job['id']} - {job.get('title', 'Untitled')}")
                except Exception as e:
                    errors.append(f"Failed to enqueue pending job {job['id']}: {str(e)}")
                    logger.error(f"[WORKER] Failed to recover pending job {job['id']}: {e}")

        # Query for processing jobs (these were interrupted by server restart)
        processing_jobs_db = db.client.table("jobs").select("id, title, status").eq(
            "status", "processing"
        ).execute()

        if processing_jobs_db.data:
            for job in processing_jobs_db.data:
                try:
                    # Reset to pending status before re-enqueueing
                    db.update_job(job["id"], {
                        "status": "pending",
                        "progress_percent": 0.0,
                        "current_step": "Recovered after server restart",
                        "error_message": None,
                    })
                    await enqueue_job(job["id"])
                    recovered_processing += 1
                    recovered_job_ids.append(job["id"])
                    logger.info(f"[WORKER] Recovered interrupted job: {job['id']} - {job.get('title', 'Untitled')}")
                except Exception as e:
                    errors.append(f"Failed to enqueue processing job {job['id']}: {str(e)}")
                    logger.error(f"[WORKER] Failed to recover processing job {job['id']}: {e}")

        total_recovered = recovered_pending + recovered_processing

        if total_recovered > 0:
            logger.info(f"[WORKER] Job recovery complete: {total_recovered} jobs recovered")
            logger.info(f"[WORKER]   - Pending jobs: {recovered_pending}")
            logger.info(f"[WORKER]   - Interrupted jobs: {recovered_processing}")
        else:
            logger.info("[WORKER] Job recovery complete: No jobs to recover")

        return {
            "recovered_pending": recovered_pending,
            "recovered_processing": recovered_processing,
            "total_recovered": total_recovered,
            "recovered_job_ids": recovered_job_ids,
            "errors": errors,
        }

    except Exception as e:
        logger.error(f"[WORKER] Job recovery failed: {e}")
        logger.error(traceback.format_exc())
        return {
            "recovered_pending": 0,
            "recovered_processing": 0,
            "total_recovered": 0,
            "recovered_job_ids": [],
            "errors": [f"Recovery scan failed: {str(e)}"],
        }


def get_worker_health() -> Dict[str, Any]:
    """
    Get worker health status for monitoring.

    Returns:
        Dictionary with worker health information
    """
    queue_status = get_queue_status()

    return {
        "worker_running": _worker_running,
        "queued_jobs": queue_status["queued_jobs"],
        "processing_jobs": queue_status["processing_jobs"],
        "processing_job_ids": queue_status["processing_job_ids"],
        "total_jobs": queue_status["total"],
        "pydub_available": PYDUB_AVAILABLE,
        "temp_directory": str(tempfile.gettempdir()),
    }
