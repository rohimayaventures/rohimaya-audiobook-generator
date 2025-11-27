"""
Background Worker for Audiobook Generation
Processes jobs asynchronously using asyncio
"""

import os
import asyncio
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv

from .database import db

# Load environment variables (only for local development)
# In production (Railway), env vars are set directly
env_path = Path(__file__).parent.parent.parent.parent / "env" / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

# Job queue
job_queue: asyncio.Queue = asyncio.Queue()
processing_jobs: set = set()


async def enqueue_job(job_id: str):
    """
    Add job to processing queue

    Args:
        job_id: Job UUID to process
    """
    await job_queue.put(job_id)
    print(f"📥 Job {job_id} added to queue")


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
    try:
        # Add to processing set
        processing_jobs.add(job_id)

        # Fetch job from database
        job = db.get_job(job_id)
        if not job:
            print(f"❌ Job {job_id} not found in database")
            return

        print(f"🔄 Processing job {job_id}: {job['title']}")

        # Update status to processing
        db.update_job(job_id, {
            "status": "processing",
            "started_at": datetime.utcnow().isoformat(),
        })

        # Download manuscript from storage
        manuscript_data = db.download_manuscript(job["source_path"])
        manuscript_text = manuscript_data.decode("utf-8")

        print(f"📄 Downloaded manuscript: {len(manuscript_text)} characters")

        # Determine which pipeline to use
        mode = job["mode"]
        tts_provider = job["tts_provider"]

        # Import pipelines
        if mode == "single_voice":
            from pipelines.standard_single_voice import generate_single_voice_audiobook

            # Prepare output directory
            output_dir = Path(f"/tmp/{job_id}")
            output_dir.mkdir(parents=True, exist_ok=True)

            # Get API key based on provider
            if tts_provider == "openai":
                api_key = os.getenv("OPENAI_API_KEY")
            elif tts_provider == "elevenlabs":
                api_key = os.getenv("ELEVENLABS_API_KEY")
            elif tts_provider == "inworld":
                api_key = os.getenv("INWORLD_JWT_KEY")
            else:
                raise ValueError(f"Unknown TTS provider: {tts_provider}")

            # Run pipeline
            print(f"🎙️ Running single-voice pipeline with {tts_provider}")
            audio_files = await asyncio.to_thread(
                generate_single_voice_audiobook,
                manuscript_text,
                output_dir,
                api_key,
                job["narrator_voice_id"],
                tts_provider,
            )

        elif mode == "dual_voice":
            from pipelines.phoenix_peacock_dual_voice import generate_dual_voice_audiobook

            # Prepare output directory
            output_dir = Path(f"/tmp/{job_id}")
            output_dir.mkdir(parents=True, exist_ok=True)

            # Get API key (dual-voice uses ElevenLabs)
            api_key = os.getenv("ELEVENLABS_API_KEY")

            # Run pipeline
            print(f"🎭 Running dual-voice pipeline")
            audio_files = await asyncio.to_thread(
                generate_dual_voice_audiobook,
                manuscript_text,
                output_dir,
                api_key,
                job["narrator_voice_id"],
                job["character_voice_id"],
                job["character_name"],
            )

        else:
            raise ValueError(f"Unknown mode: {mode}")

        # Upload final audio to storage
        final_audio_path = audio_files[-1] if audio_files else None
        if not final_audio_path or not Path(final_audio_path).exists():
            raise FileNotFoundError("No final audio file generated")

        print(f"📤 Uploading final audio: {final_audio_path}")

        # Read final audio file
        with open(final_audio_path, "rb") as f:
            audio_content = f.read()

        # Upload to Supabase Storage
        storage_path = db.upload_audiobook(
            user_id=job["user_id"],
            job_id=job_id,
            filename=f"{job['title']}_COMPLETE.mp3",
            file_content=audio_content,
        )

        # Get file stats
        file_size = Path(final_audio_path).stat().st_size

        # TODO: Calculate duration (requires ffprobe or pydub)
        duration_seconds = 0

        # Update job to completed
        db.update_job(job_id, {
            "status": "completed",
            "audio_path": storage_path,
            "file_size_bytes": file_size,
            "duration_seconds": duration_seconds,
            "progress_percent": 100.0,
            "completed_at": datetime.utcnow().isoformat(),
        })

        print(f"✅ Job {job_id} completed successfully")

        # Clean up temp files
        import shutil
        if output_dir.exists():
            shutil.rmtree(output_dir)

    except Exception as e:
        # Log error
        error_message = f"{type(e).__name__}: {str(e)}"
        print(f"❌ Job {job_id} failed: {error_message}")
        print(traceback.format_exc())

        # Update job to failed
        db.update_job(job_id, {
            "status": "failed",
            "error_message": error_message,
            "completed_at": datetime.utcnow().isoformat(),
        })

    finally:
        # Remove from processing set
        processing_jobs.discard(job_id)


async def worker_loop():
    """
    Main worker loop that processes jobs from the queue
    Run this as a background task in FastAPI
    """
    print("🚀 Background worker started")

    while True:
        try:
            # Get job from queue (wait if empty)
            job_id = await job_queue.get()

            try:
                # Skip if already processing
                if job_id in processing_jobs:
                    print(f"⏭️ Job {job_id} already processing, skipping")
                    continue

                # Process job
                await process_job(job_id)

            finally:
                # Always mark task as done, even if skipped or errored
                job_queue.task_done()

        except Exception as e:
            print(f"❌ Worker error: {e}")
            print(traceback.format_exc())
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
        "total": job_queue.qsize() + len(processing_jobs),
    }
