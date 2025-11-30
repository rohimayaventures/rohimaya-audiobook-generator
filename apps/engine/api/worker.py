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
from .email import send_job_completed_email, send_job_failed_email, is_email_configured

# Import chapter parser
from core.chapter_parser import split_into_chapters, clean_text

# Words per minute for duration estimation (average narration speed)
WORDS_PER_MINUTE = 150

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

# Retry configuration
MAX_AUTO_RETRIES = 3  # Maximum automatic retries before marking as failed
RETRY_BASE_DELAY = 30  # Base delay in seconds (doubles with each retry)

# Transient errors that should trigger automatic retry
TRANSIENT_ERROR_PATTERNS = [
    "rate limit",
    "429",
    "503",
    "502",
    "timeout",
    "timed out",
    "connection reset",
    "connection refused",
    "temporarily unavailable",
    "server error",
    "resource exhausted",
    "quota exceeded",
]


def is_transient_error(error_message: str) -> bool:
    """
    Check if an error is transient and should trigger automatic retry.

    Args:
        error_message: The error message string

    Returns:
        True if the error appears to be transient
    """
    error_lower = error_message.lower()
    return any(pattern in error_lower for pattern in TRANSIENT_ERROR_PATTERNS)


def extract_text_from_file(file_content: bytes, source_path: str) -> str:
    """
    Extract text from various file formats (DOCX, PDF, TXT, MD, HTML).

    Args:
        file_content: Raw file bytes
        source_path: Original file path (to determine extension)

    Returns:
        Extracted text content

    Raises:
        ValueError: If file format is unsupported or extraction fails
    """
    import io

    # Determine file extension from source path
    ext = Path(source_path).suffix.lower() if source_path else ""

    logger.info(f"[EXTRACT] Extracting text from file with extension: {ext}")

    # Plain text formats - just decode
    if ext in (".txt", ".md", ".markdown", ".text"):
        # Try multiple encodings
        for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252", "iso-8859-1"]:
            try:
                text = file_content.decode(encoding)
                logger.info(f"[EXTRACT] Decoded text file with encoding: {encoding}")
                return text
            except UnicodeDecodeError:
                continue
        # Last resort
        text = file_content.decode("utf-8", errors="ignore")
        logger.warning("[EXTRACT] Decoded text file with utf-8 (errors ignored)")
        return text

    # DOCX files - extract from XML in ZIP with heading detection
    elif ext == ".docx":
        try:
            import zipfile
            import xml.etree.ElementTree as ET

            logger.info("[EXTRACT] Extracting text from DOCX file with heading detection")
            text_parts = []
            chapter_count = 0

            # Word XML namespace
            W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

            with zipfile.ZipFile(io.BytesIO(file_content)) as zf:
                # First, try to read styles.xml to understand heading definitions
                style_to_heading = {}
                try:
                    if "word/styles.xml" in zf.namelist():
                        with zf.open("word/styles.xml") as styles_xml:
                            styles_tree = ET.parse(styles_xml)
                            styles_root = styles_tree.getroot()
                            # Find heading styles
                            for style in styles_root.iter(f"{W_NS}style"):
                                style_id = style.get(f"{W_NS}styleId", "")
                                style_name_elem = style.find(f"{W_NS}name")
                                if style_name_elem is not None:
                                    style_name = style_name_elem.get(f"{W_NS}val", "").lower()
                                    # Check for heading styles
                                    if "heading" in style_name or "title" in style_name:
                                        style_to_heading[style_id] = style_name
                                        logger.debug(f"[EXTRACT] Found heading style: {style_id} -> {style_name}")
                except Exception as style_err:
                    logger.debug(f"[EXTRACT] Could not parse styles.xml: {style_err}")

                # Read document.xml
                with zf.open("word/document.xml") as doc_xml:
                    tree = ET.parse(doc_xml)
                    root = tree.getroot()

                    # Iterate through paragraphs to preserve structure
                    for para in root.iter(f"{W_NS}p"):
                        para_texts = []
                        is_heading = False
                        heading_level = 0

                        # Check paragraph properties for style
                        pPr = para.find(f"{W_NS}pPr")
                        if pPr is not None:
                            # Check for direct heading style (pStyle)
                            pStyle = pPr.find(f"{W_NS}pStyle")
                            if pStyle is not None:
                                style_val = pStyle.get(f"{W_NS}val", "")
                                # Check against known heading patterns
                                style_lower = style_val.lower()
                                if style_val in style_to_heading:
                                    is_heading = True
                                    # Extract level from style name if present
                                    for lvl in range(1, 10):
                                        if str(lvl) in style_to_heading[style_val]:
                                            heading_level = lvl
                                            break
                                elif "heading" in style_lower or "title" in style_lower:
                                    is_heading = True
                                    # Try to extract level number
                                    import re
                                    lvl_match = re.search(r'(\d+)', style_val)
                                    if lvl_match:
                                        heading_level = int(lvl_match.group(1))

                            # Check for outline level (another way Word marks headings)
                            outlineLvl = pPr.find(f"{W_NS}outlineLvl")
                            if outlineLvl is not None:
                                is_heading = True
                                heading_level = int(outlineLvl.get(f"{W_NS}val", "0")) + 1

                        # Extract text from paragraph
                        for t in para.iter(f"{W_NS}t"):
                            if t.text:
                                para_texts.append(t.text)

                        if para_texts:
                            para_text = "".join(para_texts)

                            # If it's a heading, add chapter marker
                            if is_heading and heading_level <= 2:
                                # Check if text already contains "Chapter" or similar
                                text_lower = para_text.lower().strip()
                                has_chapter_marker = any(marker in text_lower for marker in [
                                    "chapter", "part", "prologue", "epilogue",
                                    "introduction", "preface", "afterword"
                                ])

                                if not has_chapter_marker:
                                    # Add "CHAPTER X:" prefix to help parser
                                    chapter_count += 1
                                    para_text = f"CHAPTER {chapter_count}: {para_text}"
                                    logger.debug(f"[EXTRACT] Detected heading as chapter: {para_text[:50]}...")

                            text_parts.append(para_text)

            text = "\n\n".join(text_parts)
            logger.info(f"[EXTRACT] Extracted {len(text)} chars from DOCX ({len(text_parts)} paragraphs, {chapter_count} headings converted to chapters)")
            return text

        except Exception as e:
            logger.error(f"[EXTRACT] DOCX extraction failed: {e}")
            raise ValueError(f"Failed to extract text from DOCX: {e}")

    # PDF files - use PyPDF2
    elif ext == ".pdf":
        try:
            import PyPDF2

            logger.info("[EXTRACT] Extracting text from PDF file")
            reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            text_parts = []

            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
                logger.debug(f"[EXTRACT] PDF page {i+1}: {len(page_text) if page_text else 0} chars")

            text = "\n\n".join(text_parts)
            logger.info(f"[EXTRACT] Extracted {len(text)} chars from PDF ({len(reader.pages)} pages)")
            return text

        except Exception as e:
            logger.error(f"[EXTRACT] PDF extraction failed: {e}")
            raise ValueError(f"Failed to extract text from PDF: {e}")

    # HTML files - strip tags
    elif ext in (".html", ".htm"):
        try:
            import re

            logger.info("[EXTRACT] Extracting text from HTML file")
            # Decode first
            html = file_content.decode("utf-8", errors="ignore")

            # Remove script and style elements
            html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
            html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)

            # Replace block elements with newlines
            html = re.sub(r'<(p|div|br|h[1-6]|li)[^>]*>', '\n', html, flags=re.IGNORECASE)

            # Remove all remaining tags
            text = re.sub(r'<[^>]+>', '', html)

            # Clean up whitespace
            text = re.sub(r'\n\s*\n', '\n\n', text)
            text = text.strip()

            logger.info(f"[EXTRACT] Extracted {len(text)} chars from HTML")
            return text

        except Exception as e:
            logger.error(f"[EXTRACT] HTML extraction failed: {e}")
            raise ValueError(f"Failed to extract text from HTML: {e}")

    # EPUB files - basic extraction
    elif ext == ".epub":
        try:
            import zipfile
            import re

            logger.info("[EXTRACT] Extracting text from EPUB file")
            text_parts = []

            with zipfile.ZipFile(io.BytesIO(file_content)) as zf:
                for name in zf.namelist():
                    if name.endswith(('.xhtml', '.html', '.htm')):
                        with zf.open(name) as f:
                            html = f.read().decode("utf-8", errors="ignore")
                            # Strip HTML tags
                            text = re.sub(r'<[^>]+>', '', html)
                            text = re.sub(r'\s+', ' ', text).strip()
                            if text:
                                text_parts.append(text)

            text = "\n\n".join(text_parts)
            logger.info(f"[EXTRACT] Extracted {len(text)} chars from EPUB")
            return text

        except Exception as e:
            logger.error(f"[EXTRACT] EPUB extraction failed: {e}")
            raise ValueError(f"Failed to extract text from EPUB: {e}")

    else:
        # Unknown format - try to decode as text
        logger.warning(f"[EXTRACT] Unknown file format '{ext}', attempting text decode")
        for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
            try:
                text = file_content.decode(encoding)
                # Check if it looks like text (not binary garbage)
                if text.isprintable() or '\n' in text:
                    logger.info(f"[EXTRACT] Decoded unknown format as text with {encoding}")
                    return text
            except UnicodeDecodeError:
                continue

        raise ValueError(
            f"Unsupported file format: {ext}. "
            f"Please upload a TXT, DOCX, PDF, MD, HTML, or EPUB file."
        )


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


def get_user_info(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get user info from Supabase for email notifications.

    Args:
        user_id: User UUID

    Returns:
        Dictionary with user email and name, or None if not found
    """
    try:
        # Query user profile from Supabase
        result = db.client.table("profiles").select("email, full_name, display_name").eq(
            "id", user_id
        ).single().execute()

        if result.data:
            user = result.data
            # Get display name (fallback to full_name, then email prefix)
            display_name = (
                user.get("display_name") or
                user.get("full_name") or
                user.get("email", "").split("@")[0] or
                "User"
            )
            return {
                "email": user.get("email"),
                "name": display_name,
            }
    except Exception as e:
        logger.warning(f"[EMAIL] Could not fetch user info for {user_id}: {e}")

    return None


async def send_job_notification(job_id: str, job: Dict[str, Any], success: bool, error_message: Optional[str] = None):
    """
    Send email notification for job completion/failure.

    Args:
        job_id: Job UUID
        job: Job data dictionary
        success: Whether job completed successfully
        error_message: Error message if job failed
    """
    if not is_email_configured():
        logger.debug("[EMAIL] Email not configured, skipping notification")
        return

    user_info = get_user_info(job["user_id"])
    if not user_info or not user_info.get("email"):
        logger.warning(f"[EMAIL] No email found for user {job['user_id']}, skipping notification")
        return

    try:
        if success:
            # Calculate duration in minutes
            duration_seconds = job.get("duration_seconds", 0)
            duration_minutes = max(1, duration_seconds // 60)

            await send_job_completed_email(
                to_email=user_info["email"],
                to_name=user_info["name"],
                job_title=job.get("title", "Untitled"),
                job_id=job_id,
                duration_minutes=duration_minutes,
            )
            logger.info(f"[EMAIL] Sent completion email to {user_info['email']} for job {job_id}")
        else:
            await send_job_failed_email(
                to_email=user_info["email"],
                to_name=user_info["name"],
                job_title=job.get("title", "Untitled"),
                job_id=job_id,
                error_message=error_message or "Unknown error",
            )
            logger.info(f"[EMAIL] Sent failure email to {user_info['email']} for job {job_id}")

    except Exception as e:
        # Don't fail the job if email fails
        logger.error(f"[EMAIL] Failed to send notification email: {e}")


async def parse_and_save_chapters(job_id: str, manuscript_text: str) -> List[Dict[str, Any]]:
    """
    Parse manuscript into chapters and save them to the database.

    This function:
    1. Uses chapter_parser to detect chapters
    2. Saves each chapter to the 'chapters' table
    3. Returns list of saved chapter records

    Args:
        job_id: Job UUID
        manuscript_text: Full manuscript text

    Returns:
        List of chapter records saved to database
    """
    import uuid

    logger.info(f"[PARSE] {job_id} - Parsing manuscript into chapters...")

    # Parse chapters using the chapter parser
    parsed_chapters = split_into_chapters(manuscript_text)

    if not parsed_chapters:
        logger.warning(f"[PARSE] {job_id} - No chapters detected, creating single chapter")
        # Create a single chapter for the entire manuscript
        text = clean_text(manuscript_text)
        word_count = len(text.split())
        parsed_chapters = [{
            "index": 1,
            "source_order": 0,
            "chapter_index": 0,
            "title": "Full Manuscript",
            "text": text,
            "segment_type": "body_chapter",
            "pattern_type": "single_chapter",
            "word_count": word_count,
            "character_count": len(text),
        }]

    logger.info(f"[PARSE] {job_id} - Detected {len(parsed_chapters)} chapter(s)")

    # Save each chapter to database
    saved_chapters = []

    for chapter in parsed_chapters:
        word_count = chapter.get("word_count", 0)
        # Estimate duration: ~150 words per minute for narration
        estimated_duration = int((word_count / WORDS_PER_MINUTE) * 60)

        chapter_data = {
            "id": str(uuid.uuid4()),
            "job_id": job_id,
            "source_order": chapter["source_order"],
            "chapter_index": chapter["chapter_index"],
            "title": chapter["title"],
            "display_title": chapter.get("title", f"Chapter {chapter['index']}"),
            "text_content": chapter["text"],
            "segment_type": chapter.get("segment_type", "body_chapter"),
            "word_count": word_count,
            "character_count": chapter.get("character_count", len(chapter.get("text", ""))),
            "estimated_duration_seconds": estimated_duration,
            "status": "pending_review",
            "created_at": datetime.utcnow().isoformat(),
        }

        try:
            result = db.client.table("chapters").insert(chapter_data).execute()
            if result.data:
                saved_chapters.append(result.data[0])
                logger.debug(f"[PARSE] {job_id} - Saved chapter: {chapter['title']} ({word_count} words)")
        except Exception as e:
            logger.error(f"[PARSE] {job_id} - Failed to save chapter {chapter['title']}: {e}")
            raise

    logger.info(f"[PARSE] {job_id} - Successfully saved {len(saved_chapters)} chapters to database")
    return saved_chapters


def get_approved_chapters(job_id: str) -> List[Dict[str, Any]]:
    """
    Get all approved chapters for a job, ordered by chapter_index.

    Args:
        job_id: Job UUID

    Returns:
        List of approved chapter records
    """
    try:
        result = db.client.table("chapters").select("*").eq(
            "job_id", job_id
        ).eq(
            "status", "approved"
        ).order("chapter_index").execute()

        return result.data or []
    except Exception as e:
        logger.error(f"[CHAPTERS] Failed to get approved chapters for {job_id}: {e}")
        return []


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

    This function handles a two-phase workflow:

    Phase 1 (pending → chapters_pending):
    1. Fetches job from database
    2. Downloads manuscript from storage
    3. Parses manuscript into chapters
    4. Saves chapters to database
    5. Updates job status to 'chapters_pending' (waits for user approval)

    Phase 2 (chapters_approved → processing → completed):
    1. Gets approved chapters from database
    2. Runs TTS pipeline for each chapter
    3. Uploads generated audio to storage
    4. Updates job status to completed
    """
    output_dir = None
    job = None  # Initialize for email notification in except block

    try:
        # Add to processing set
        processing_jobs.add(job_id)

        # Fetch job from database
        job = db.get_job(job_id)
        if not job:
            logger.error(f"[JOB] {job_id} - Not found in database")
            return

        # Check if job was cancelled before we started
        if job["status"] == "cancelled":
            logger.info(f"[JOB] {job_id} - Already cancelled, skipping")
            return

        job_status = job["status"]
        logger.info(f"[JOB] {job_id} - Starting: {job['title']} (status: {job_status})")
        logger.info(f"[JOB] {job_id} - Mode: {job['mode']}, Provider: {job['tts_provider']}, Voice: {job.get('narrator_voice_id')}")

        # ======================================================================
        # PHASE 1: PARSE CHAPTERS (pending → chapters_pending)
        # ======================================================================
        if job_status == "pending":
            logger.info(f"[JOB] {job_id} - Phase 1: Parsing manuscript into chapters")

            # Update status to parsing
            db.update_job(job_id, {
                "status": "parsing",
                "started_at": datetime.utcnow().isoformat(),
                "progress_percent": 5.0,
                "current_step": "Downloading manuscript...",
            })

            # Download manuscript from storage
            source_path = job.get("source_path")
            if not source_path:
                raise ValueError("No source_path found for job - manuscript not uploaded")

            logger.info(f"[JOB] {job_id} - Downloading manuscript from: {source_path}")
            manuscript_data = db.download_manuscript(source_path)

            # Extract text from file (handles DOCX, PDF, TXT, MD, HTML, EPUB)
            db.update_job(job_id, {
                "progress_percent": 15.0,
                "current_step": "Extracting text from file...",
            })
            manuscript_text = extract_text_from_file(manuscript_data, source_path)

            word_count = len(manuscript_text.split())
            logger.info(f"[JOB] {job_id} - Manuscript extracted: {len(manuscript_text)} chars, ~{word_count} words")

            # Parse chapters and save to database
            db.update_job(job_id, {
                "progress_percent": 30.0,
                "current_step": "Detecting chapters...",
            })
            chapters = await parse_and_save_chapters(job_id, manuscript_text)

            # Calculate totals
            total_words = sum(ch.get("word_count", 0) for ch in chapters)
            total_duration = sum(ch.get("estimated_duration_seconds", 0) for ch in chapters)

            # Update job to chapters_pending status
            # Note: total_chapters is the only extra column that exists in the jobs table
            db.update_job(job_id, {
                "status": "chapters_pending",
                "progress_percent": 50.0,
                "current_step": f"Waiting for chapter review ({len(chapters)} chapters, ~{total_duration // 60}min)",
                "total_chapters": len(chapters),
            })

            logger.info(f"[JOB] {job_id} - Phase 1 complete: {len(chapters)} chapters detected")
            logger.info(f"[JOB] {job_id} - Waiting for user to review and approve chapters")

            # Phase 1 complete - job will wait for user to approve chapters
            return

        # ======================================================================
        # PHASE 2: GENERATE AUDIO (chapters_approved → processing → completed)
        # ======================================================================
        if job_status != "chapters_approved":
            logger.warning(f"[JOB] {job_id} - Unexpected status '{job_status}', skipping")
            return

        logger.info(f"[JOB] {job_id} - Phase 2: Generating audio from approved chapters")

        # Update status to processing
        db.update_job(job_id, {
            "status": "processing",
            "progress_percent": 5.0,
            "current_step": "Starting audio generation...",
        })

        # Get approved chapters from database
        approved_chapters = get_approved_chapters(job_id)
        if not approved_chapters:
            raise ValueError("No approved chapters found for this job")

        logger.info(f"[JOB] {job_id} - Found {len(approved_chapters)} approved chapters")

        # Build manuscript text from approved chapters in order
        manuscript_text = "\n\n".join(
            ch.get("text_content", "") for ch in approved_chapters
        )

        word_count = len(manuscript_text.split())
        logger.info(f"[JOB] {job_id} - Combined manuscript: {len(manuscript_text)} chars, ~{word_count} words")

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
            # Check if Gemini TTS is available (preferred for multilingual support)
            google_genai_key = os.getenv("GOOGLE_GENAI_API_KEY")
            openai_api_key = os.getenv("OPENAI_API_KEY")

            # Get language settings from job (with defaults for backwards compatibility)
            input_language = job.get("input_language_code", "en-US")
            # IMPORTANT: Do NOT fallback output_language to input_language here!
            # If output_language_code is None, it means "same as input" - the TTS module
            # needs to see None to know translation wasn't requested.
            output_language = job.get("output_language_code")  # Can be None
            voice_preset_id = job.get("voice_preset_id") or job.get("narrator_voice_id", "studio_neutral")
            emotion_style = job.get("emotion_style_prompt")
            audio_format = job.get("audio_format", "mp3")

            # Use Gemini TTS if available (recommended for multilingual)
            if google_genai_key and tts_provider in ("google", "gemini"):
                from pipelines.gemini_single_voice import generate_gemini_audiobook

                logger.info(f"[JOB] {job_id} - Using Gemini TTS (multilingual)")
                logger.info(f"[JOB] {job_id} - Voice preset: {voice_preset_id}")
                logger.info(f"[JOB] {job_id} - Input language: {input_language}")
                logger.info(f"[JOB] {job_id} - Output language: {output_language}")
                logger.info(f"[JOB] {job_id} - Audio format: {audio_format}")
                if emotion_style:
                    logger.info(f"[JOB] {job_id} - Emotion/style: {emotion_style}")

                db.update_job(job_id, {"progress_percent": 15.0})

                # Progress callback to update job
                def progress_callback(percent: float, message: str):
                    # Scale progress from 15% to 80%
                    scaled = 15 + (percent / 100 * 65)
                    db.update_job(job_id, {
                        "progress_percent": scaled,
                        "current_step": message,
                    })

                audio_files = await generate_gemini_audiobook(
                    manuscript_text=manuscript_text,
                    output_dir=output_dir,
                    voice_preset_id=voice_preset_id,
                    input_language_code=input_language,
                    output_language_code=output_language,
                    emotion_style_prompt=emotion_style,
                    audio_format=audio_format,
                    book_title=job["title"],
                    progress_callback=progress_callback,
                )

            elif openai_api_key:
                # Fallback to OpenAI TTS (legacy path)
                from pipelines.standard_single_voice import generate_single_voice_audiobook

                logger.info(f"[JOB] {job_id} - Using OpenAI TTS (fallback)")

                db.update_job(job_id, {"progress_percent": 15.0})

                audio_files = await asyncio.to_thread(
                    generate_single_voice_audiobook,
                    manuscript_text,
                    output_dir,
                    openai_api_key,
                    job["narrator_voice_id"],
                    "openai",
                    job["title"],
                )

            else:
                raise ValueError("No TTS API key configured. Set GOOGLE_GENAI_API_KEY or OPENAI_API_KEY")

        elif mode == "dual_voice":
            from pipelines.phoenix_peacock_dual_voice import generate_dual_voice_audiobook

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
            from pipelines.findaway_pipeline import generate_findaway_audiobook

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

            # Send completion email notification
            job["duration_seconds"] = duration_seconds  # Add for email
            await send_job_notification(job_id, job, success=True)

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

        # Send completion email notification
        job["duration_seconds"] = duration_seconds  # Add for email
        await send_job_notification(job_id, job, success=True)

    except Exception as e:
        # Log error with full traceback
        error_message = f"{type(e).__name__}: {str(e)}"
        logger.error(f"[JOB] {job_id} - Failed: {error_message}")
        logger.error(traceback.format_exc())

        # Check if this is a transient error that should be auto-retried
        current_retry_count = job.get("retry_count", 0) if job else 0
        should_auto_retry = (
            is_transient_error(error_message) and
            current_retry_count < MAX_AUTO_RETRIES and
            job is not None
        )

        if should_auto_retry:
            # Calculate exponential backoff delay
            retry_delay = RETRY_BASE_DELAY * (2 ** current_retry_count)
            next_retry = current_retry_count + 1

            logger.info(f"[JOB] {job_id} - Transient error detected, scheduling auto-retry {next_retry}/{MAX_AUTO_RETRIES} in {retry_delay}s")

            # Update job for retry
            db.update_job(job_id, {
                "status": "pending",
                "error_message": f"Auto-retry {next_retry}/{MAX_AUTO_RETRIES} scheduled (previous error: {error_message})",
                "progress_percent": 0.0,
                "current_step": f"Waiting {retry_delay}s before retry...",
                "retry_count": next_retry,
            })

            # Schedule delayed retry
            async def delayed_retry():
                await asyncio.sleep(retry_delay)
                await enqueue_job(job_id)
                logger.info(f"[JOB] {job_id} - Auto-retry {next_retry} enqueued after {retry_delay}s delay")

            asyncio.create_task(delayed_retry())

        else:
            # Permanent failure - update job and send email
            final_message = error_message
            if current_retry_count >= MAX_AUTO_RETRIES:
                final_message = f"Max retries ({MAX_AUTO_RETRIES}) exceeded. Last error: {error_message}"
                logger.error(f"[JOB] {job_id} - Max auto-retries exceeded")

            db.update_job(job_id, {
                "status": "failed",
                "error_message": final_message,
                "completed_at": datetime.utcnow().isoformat(),
            })

            # Send failure email notification
            if job:
                await send_job_notification(job_id, job, success=False, error_message=final_message)

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
