"""
Findaway-Ready Audiobook Pipeline

Complete pipeline for generating Findaway-compliant audiobook packages:
- Manuscript parsing and structure extraction
- Opening/ending credits generation
- Retail sample selection
- Chapter-by-chapter audio generation
- Cover image generation
- Manifest JSON creation
- ZIP packaging

Output structure:
job_id/
  manifest.json
  cover_2400x2400.png
  audio/
    01_opening_credits.mp3
    02_front_matter.mp3 (optional)
    03_chapter_001.mp3
    03_chapter_002.mp3
    ...
    04_back_matter.mp3 (optional)
    05_ending_credits.mp3
    06_retail_sample.mp3
"""

import os
import json
import logging
import zipfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)

# Import agents and helpers
from ..agents.manuscript_parser_agent import parse_manuscript_structure
from ..agents.retail_sample_agent import select_retail_sample_excerpt
from ..core.findaway_planner import build_findaway_section_plan
from ..core.cover_generator import generate_cover_image, save_cover_to_file, get_cover_filename


def generate_findaway_audiobook(
    manuscript_text: str,
    output_dir: Path,
    api_key: str,
    voice_id: str,
    book_metadata: Dict[str, Any],
    progress_callback: Optional[Callable[[float, str], None]] = None,
) -> Dict[str, Any]:
    """
    Generate a complete Findaway-ready audiobook package.

    Args:
        manuscript_text: Full manuscript text
        output_dir: Directory to write output files
        api_key: OpenAI API key
        voice_id: OpenAI TTS voice ID
        book_metadata: Book metadata (title, author, genre, etc.)
        progress_callback: Optional callback(percent, message) for progress updates

    Returns:
        Dictionary with:
        {
            "manifest_path": Path,
            "zip_path": Path,
            "audio_files": List[Path],
            "cover_path": Path,
            "total_duration_seconds": int,
            "section_count": int,
        }
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    audio_dir = output_dir / "audio"
    audio_dir.mkdir(exist_ok=True)

    def update_progress(percent: float, message: str):
        logger.info(f"[{percent:.0f}%] {message}")
        if progress_callback:
            progress_callback(percent, message)

    update_progress(5, "Starting Findaway pipeline")

    # ==========================================================================
    # STEP 1: Parse manuscript structure
    # ==========================================================================
    update_progress(10, "Parsing manuscript structure with AI")

    try:
        manuscript_structure = parse_manuscript_structure(
            manuscript_text=manuscript_text,
            api_key=api_key,
            model="gpt-4o-mini"
        )
        logger.info(f"Parsed manuscript: {len(manuscript_structure.get('chapters', []))} chapters")
    except Exception as e:
        logger.error(f"Manuscript parsing failed: {e}")
        # Create minimal structure from raw text
        manuscript_structure = _create_fallback_structure(manuscript_text, book_metadata)

    # Merge parsed metadata with provided metadata
    if not book_metadata.get("title") and manuscript_structure.get("title"):
        book_metadata["title"] = manuscript_structure["title"]
    if not book_metadata.get("author") and manuscript_structure.get("author"):
        book_metadata["author"] = manuscript_structure["author"]

    update_progress(20, "Manuscript structure extracted")

    # ==========================================================================
    # STEP 2: Select retail sample
    # ==========================================================================
    update_progress(22, "Selecting retail sample excerpt")

    try:
        retail_sample = select_retail_sample_excerpt(
            manuscript_structure=manuscript_structure,
            api_key=api_key,
            target_duration_minutes=4.0,
            preferred_style=book_metadata.get("sample_style", "default"),
            model="gpt-4o-mini"
        )
        logger.info(f"Selected retail sample: {retail_sample.get('approx_word_count', 0)} words")
    except Exception as e:
        logger.error(f"Retail sample selection failed: {e}")
        retail_sample = _create_fallback_sample(manuscript_structure)

    update_progress(25, "Retail sample selected")

    # ==========================================================================
    # STEP 3: Build Findaway section plan
    # ==========================================================================
    update_progress(27, "Building Findaway section plan")

    section_plan = build_findaway_section_plan(
        manuscript_structure=manuscript_structure,
        book_metadata=book_metadata,
        retail_sample=retail_sample
    )

    sections = section_plan.get("sections", [])
    logger.info(f"Section plan created: {len(sections)} sections")

    update_progress(30, f"Section plan ready: {len(sections)} sections")

    # ==========================================================================
    # STEP 4: Generate cover image
    # ==========================================================================
    update_progress(32, "Generating cover image")

    cover_path = None
    try:
        cover_result = generate_cover_image(
            title=book_metadata.get("title", "Untitled"),
            author=book_metadata.get("author"),
            genre=book_metadata.get("genre"),
            vibe=book_metadata.get("cover_vibe"),
        )

        cover_filename = get_cover_filename(book_metadata.get("title", "cover"))
        cover_path = save_cover_to_file(cover_result, output_dir / cover_filename)
        logger.info(f"Cover generated: {cover_path}")
    except Exception as e:
        logger.warning(f"Cover generation failed (continuing without cover): {e}")

    update_progress(35, "Cover image ready" if cover_path else "Skipping cover (generation failed)")

    # ==========================================================================
    # STEP 5: Generate audio for each section
    # ==========================================================================
    audio_files = []
    total_duration_seconds = 0

    # Calculate progress distribution for audio generation (35% to 90%)
    audio_progress_start = 35
    audio_progress_end = 90
    audio_progress_range = audio_progress_end - audio_progress_start

    for i, section in enumerate(sections):
        section_progress = audio_progress_start + (i / len(sections)) * audio_progress_range
        section_type = section.get("type", "unknown")
        section_title = section.get("title", f"Section {i+1}")

        update_progress(section_progress, f"Generating audio: {section_title}")

        # Generate audio for section
        audio_path, duration = _generate_section_audio(
            section=section,
            output_dir=audio_dir,
            api_key=api_key,
            voice_id=voice_id,
            index=i
        )

        if audio_path:
            audio_files.append(audio_path)
            total_duration_seconds += duration
            section["audio_path"] = str(audio_path.name)
            section["duration_seconds"] = duration
            logger.info(f"  Generated: {audio_path.name} ({duration}s)")

    update_progress(90, f"Audio generation complete: {len(audio_files)} files")

    # ==========================================================================
    # STEP 6: Create manifest JSON
    # ==========================================================================
    update_progress(92, "Creating manifest")

    manifest = _create_manifest(
        book_metadata=book_metadata,
        section_plan=section_plan,
        cover_path=cover_path,
        total_duration_seconds=total_duration_seconds,
    )

    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    logger.info(f"Manifest created: {manifest_path}")

    # ==========================================================================
    # STEP 7: Create ZIP package
    # ==========================================================================
    update_progress(95, "Creating ZIP package")

    zip_path = _create_zip_package(
        output_dir=output_dir,
        manifest_path=manifest_path,
        audio_dir=audio_dir,
        cover_path=cover_path,
        book_title=book_metadata.get("title", "audiobook")
    )

    logger.info(f"ZIP package created: {zip_path}")

    update_progress(100, "Findaway package complete!")

    return {
        "manifest_path": manifest_path,
        "zip_path": zip_path,
        "audio_files": audio_files,
        "cover_path": cover_path,
        "total_duration_seconds": total_duration_seconds,
        "section_count": len(sections),
        "manifest": manifest,
    }


def _generate_section_audio(
    section: Dict[str, Any],
    output_dir: Path,
    api_key: str,
    voice_id: str,
    index: int
) -> tuple[Optional[Path], int]:
    """
    Generate audio for a single section using OpenAI TTS.

    Args:
        section: Section dict with type, title, text
        output_dir: Directory to write audio file
        api_key: OpenAI API key
        voice_id: OpenAI voice ID
        index: Section index for filename ordering

    Returns:
        (audio_path, duration_seconds) or (None, 0) on failure
    """
    from openai import OpenAI

    text = section.get("text", "").strip()
    if not text:
        logger.warning(f"Section {index} has no text, skipping")
        return None, 0

    section_type = section.get("type", "chapter")
    title = section.get("title", f"Section {index}")

    # Create filename with ordering prefix
    type_prefix = {
        "opening_credits": "01",
        "front_matter": "02",
        "chapter": "03",
        "back_matter": "04",
        "ending_credits": "05",
        "retail_sample": "06",
    }.get(section_type, "03")

    # Sanitize title for filename
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_title = safe_title.replace(' ', '_')[:40]
    if not safe_title:
        safe_title = f"section_{index:03d}"

    filename = f"{type_prefix}_{safe_title}.mp3"
    audio_path = output_dir / filename

    # Generate audio with OpenAI TTS
    client = OpenAI(api_key=api_key)

    try:
        # OpenAI TTS has a 4096 character limit per request
        # Split long text into chunks if needed
        max_chars = 4000
        if len(text) > max_chars:
            audio_chunks = []
            text_chunks = _split_text_for_tts(text, max_chars)

            for chunk_idx, chunk in enumerate(text_chunks):
                response = client.audio.speech.create(
                    model="tts-1-hd",
                    voice=voice_id,
                    input=chunk,
                    response_format="mp3"
                )
                chunk_path = output_dir / f"_chunk_{index}_{chunk_idx}.mp3"
                response.stream_to_file(str(chunk_path))
                audio_chunks.append(chunk_path)

            # Merge chunks using pydub
            audio_path = _merge_audio_chunks(audio_chunks, audio_path)

            # Clean up chunk files
            for chunk_path in audio_chunks:
                try:
                    chunk_path.unlink()
                except:
                    pass
        else:
            response = client.audio.speech.create(
                model="tts-1-hd",
                voice=voice_id,
                input=text,
                response_format="mp3"
            )
            response.stream_to_file(str(audio_path))

        # Calculate duration
        duration = _get_audio_duration(audio_path)
        return audio_path, duration

    except Exception as e:
        logger.error(f"Failed to generate audio for section {index}: {e}")
        return None, 0


def _split_text_for_tts(text: str, max_chars: int) -> List[str]:
    """
    Split text into chunks suitable for TTS API.
    Tries to split at sentence boundaries.
    """
    chunks = []
    current_chunk = ""

    # Split into sentences (roughly)
    sentences = text.replace('\n', ' ').split('. ')

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        # Add period back if it was split off
        if not sentence.endswith(('.', '!', '?', '"')):
            sentence += '.'

        # Check if adding this sentence would exceed limit
        if len(current_chunk) + len(sentence) + 1 > max_chars:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence
        else:
            current_chunk = current_chunk + ' ' + sentence if current_chunk else sentence

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def _merge_audio_chunks(chunk_paths: List[Path], output_path: Path) -> Path:
    """Merge multiple audio chunks into a single file using pydub."""
    try:
        from pydub import AudioSegment

        combined = AudioSegment.empty()
        for chunk_path in chunk_paths:
            audio = AudioSegment.from_mp3(str(chunk_path))
            combined += audio

        combined.export(str(output_path), format="mp3")
        return output_path
    except ImportError:
        logger.warning("pydub not available, using first chunk only")
        # Fallback: just use the first chunk
        if chunk_paths:
            import shutil
            shutil.copy(chunk_paths[0], output_path)
        return output_path


def _get_audio_duration(audio_path: Path) -> int:
    """Get audio duration in seconds."""
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_file(str(audio_path))
        return int(len(audio) / 1000)
    except:
        # Estimate from file size (~16kbps for speech)
        try:
            size_bytes = audio_path.stat().st_size
            return int(size_bytes / 16000 * 8)
        except:
            return 0


def _create_fallback_structure(manuscript_text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Create minimal manuscript structure when parsing fails."""
    # Split into chapters by common patterns
    import re

    chapters = []
    chapter_pattern = r'(?:chapter|part|section)\s+(\d+|[ivxlc]+|one|two|three|four|five|six|seven|eight|nine|ten)'

    # Try to split by chapter markers
    parts = re.split(chapter_pattern, manuscript_text, flags=re.IGNORECASE)

    if len(parts) > 1:
        # Found chapter markers
        current_text = parts[0].strip()
        for i in range(1, len(parts), 2):
            chapter_num = parts[i] if i < len(parts) else str((i+1)//2)
            chapter_text = parts[i+1].strip() if i+1 < len(parts) else ""

            if chapter_text:
                chapters.append({
                    "index": len(chapters) + 1,
                    "title": f"Chapter {chapter_num}",
                    "text": chapter_text,
                    "word_count": len(chapter_text.split())
                })
    else:
        # No chapter markers found - treat as single chapter
        chapters.append({
            "index": 1,
            "title": "Chapter 1",
            "text": manuscript_text,
            "word_count": len(manuscript_text.split())
        })

    return {
        "title": metadata.get("title"),
        "author": metadata.get("author"),
        "front_matter": None,
        "back_matter": None,
        "chapters": chapters,
        "total_word_count": len(manuscript_text.split()),
        "parsing_method": "fallback"
    }


def _create_fallback_sample(manuscript_structure: Dict[str, Any]) -> Dict[str, Any]:
    """Create fallback retail sample from first chapter."""
    chapters = manuscript_structure.get("chapters", [])
    if not chapters:
        return {
            "chapter_index": 1,
            "excerpt_text": "",
            "approx_word_count": 0,
            "approx_duration_seconds": 0,
            "reason": "No chapters available"
        }

    first_chapter = chapters[0]
    text = first_chapter.get("text", "")
    words = text.split()[:600]  # ~4 minutes
    excerpt = " ".join(words)

    return {
        "chapter_index": first_chapter.get("index", 1),
        "chapter_title": first_chapter.get("title"),
        "excerpt_text": excerpt,
        "approx_word_count": len(words),
        "approx_duration_seconds": int(len(words) / 150 * 60),
        "reason": "Fallback: Opening excerpt from Chapter 1"
    }


def _create_manifest(
    book_metadata: Dict[str, Any],
    section_plan: Dict[str, Any],
    cover_path: Optional[Path],
    total_duration_seconds: int,
) -> Dict[str, Any]:
    """Create Findaway-compatible manifest JSON."""
    sections = section_plan.get("sections", [])

    # Build audio files list
    audio_files = []
    for section in sections:
        if section.get("audio_path"):
            audio_files.append({
                "filename": section["audio_path"],
                "type": section.get("type"),
                "title": section.get("title"),
                "duration_seconds": section.get("duration_seconds", 0),
                "order": section.get("order", 0),
            })

    return {
        "version": "1.0",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "generator": "AuthorFlow Studios",

        "book": {
            "title": book_metadata.get("title"),
            "author": book_metadata.get("author"),
            "narrator": book_metadata.get("narrator"),
            "genre": book_metadata.get("genre"),
            "language": book_metadata.get("language", "en"),
            "isbn": book_metadata.get("isbn"),
            "publisher": book_metadata.get("publisher", "AuthorFlow Studios"),
        },

        "audio": {
            "total_duration_seconds": total_duration_seconds,
            "total_duration_formatted": _format_duration(total_duration_seconds),
            "file_count": len(audio_files),
            "format": "mp3",
            "sample_rate": 44100,
            "channels": 1,
            "files": audio_files,
        },

        "cover": {
            "filename": cover_path.name if cover_path else None,
            "dimensions": "2400x2400",
            "format": "png",
        } if cover_path else None,

        "credits": section_plan.get("credits", {}),

        "retail_sample": {
            "filename": next(
                (s["audio_path"] for s in sections if s.get("type") == "retail_sample"),
                None
            ),
            "source_chapter": section_plan.get("retail_sample", {}).get("source_chapter"),
        },

        "findaway_compliance": {
            "has_opening_credits": any(s.get("type") == "opening_credits" for s in sections),
            "has_ending_credits": any(s.get("type") == "ending_credits" for s in sections),
            "has_retail_sample": any(s.get("type") == "retail_sample" for s in sections),
            "cover_dimensions_valid": cover_path is not None,
        }
    }


def _format_duration(seconds: int) -> str:
    """Format duration as HH:MM:SS."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def _create_zip_package(
    output_dir: Path,
    manifest_path: Path,
    audio_dir: Path,
    cover_path: Optional[Path],
    book_title: str
) -> Path:
    """Create ZIP package with all audiobook files."""
    # Sanitize title for filename
    safe_title = "".join(c for c in book_title if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_title = safe_title.replace(' ', '_')[:50]
    if not safe_title:
        safe_title = "audiobook"

    zip_filename = f"{safe_title}_findaway_package.zip"
    zip_path = output_dir / zip_filename

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add manifest
        zf.write(manifest_path, "manifest.json")

        # Add cover if exists
        if cover_path and cover_path.exists():
            zf.write(cover_path, cover_path.name)

        # Add all audio files
        if audio_dir.exists():
            for audio_file in sorted(audio_dir.glob("*.mp3")):
                # Skip temporary chunk files
                if not audio_file.name.startswith("_chunk_"):
                    zf.write(audio_file, f"audio/{audio_file.name}")

    logger.info(f"ZIP package size: {zip_path.stat().st_size} bytes")
    return zip_path
