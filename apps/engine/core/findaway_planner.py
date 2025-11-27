"""
Findaway Section Planner

Builds a complete audiobook section plan that's compatible with
Findaway Voices and other audiobook distribution platforms.

The plan includes:
- Opening credits
- Front matter (dedication, foreword, etc.)
- Body/chapters
- Back matter (epilogue, afterword, acknowledgements, about author)
- Ending credits
- Retail sample
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Default scripts for credits
DEFAULT_OPENING_CREDITS_TEMPLATE = """This is "{title}"{author_clause}, narrated by {narrator}, produced by AuthorFlow Studios."""

DEFAULT_ENDING_CREDITS_TEMPLATE = """This has been "{title}"{author_clause}, narrated by {narrator}. Thank you for listening. This production was created by AuthorFlow Studios."""


def build_findaway_section_plan(
    manuscript_structure: Dict[str, Any],
    book_metadata: Dict[str, Any],
    retail_sample: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Build a complete Findaway-ready section plan for audiobook production.

    Args:
        manuscript_structure: Parsed manuscript from manuscript_parser_agent
            {title, author, front_matter, chapters, back_matter}
        book_metadata: Additional metadata for the audiobook
            {narrator_name, tts_provider, voice_id, audio_format}
        retail_sample: Selected retail sample from retail_sample_agent
            {chapter_index, excerpt_text, approx_duration_seconds, ...}

    Returns:
        Complete section plan:
        {
            "opening_credits": {"status": str, "script": str, "section_id": str},
            "front_matter": [{"id": str, "status": str, "text": str, "section_id": str}, ...],
            "body_matter": [{"index": int, "title": str, "text": str, "section_id": str}, ...],
            "back_matter": [{"id": str, "status": str, "text": str, "section_id": str}, ...],
            "ending_credits": {"status": str, "script": str, "section_id": str},
            "retail_sample": {..., "section_id": str},
            "missing_sections": {"front_matter": [...], "back_matter": [...]},
            "metadata": {...}
        }
    """
    logger.info("Building Findaway section plan")

    # Extract info for credits
    title = manuscript_structure.get("title") or book_metadata.get("title", "Untitled Audiobook")
    author = manuscript_structure.get("author") or book_metadata.get("author")
    narrator = book_metadata.get("narrator_name", "AI Narrator")

    # Build opening credits
    opening_credits = _build_opening_credits(title, author, narrator)

    # Build front matter sections
    front_matter, missing_front = _build_front_matter(manuscript_structure.get("front_matter", {}))

    # Build body (chapters)
    body_matter = _build_body_matter(manuscript_structure.get("chapters", []))

    # Build back matter sections
    back_matter, missing_back = _build_back_matter(manuscript_structure.get("back_matter", {}))

    # Build ending credits
    ending_credits = _build_ending_credits(title, author, narrator)

    # Format retail sample
    formatted_sample = _format_retail_sample(retail_sample)

    # Compile plan
    plan = {
        "opening_credits": opening_credits,
        "front_matter": front_matter,
        "body_matter": body_matter,
        "back_matter": back_matter,
        "ending_credits": ending_credits,
        "retail_sample": formatted_sample,
        "missing_sections": {
            "front_matter": missing_front,
            "back_matter": missing_back,
        },
        "metadata": {
            "title": title,
            "author": author,
            "narrator": narrator,
            "tts_provider": book_metadata.get("tts_provider", "openai"),
            "voice_id": book_metadata.get("voice_id"),
            "audio_format": book_metadata.get("audio_format", "mp3"),
            "total_chapters": len(body_matter),
            "total_sections": _count_total_sections(
                opening_credits, front_matter, body_matter, back_matter, ending_credits
            ),
            "created_at": datetime.utcnow().isoformat() + "Z",
        }
    }

    logger.info(f"Section plan complete: {plan['metadata']['total_sections']} sections")
    return plan


def _build_opening_credits(title: str, author: Optional[str], narrator: str) -> Dict[str, Any]:
    """Build opening credits section."""
    author_clause = f" by {author}" if author else ""

    script = DEFAULT_OPENING_CREDITS_TEMPLATE.format(
        title=title,
        author_clause=author_clause,
        narrator=narrator
    )

    return {
        "status": "generated",
        "script": script,
        "section_id": "opening_credits",
        "section_type": "credits"
    }


def _build_ending_credits(title: str, author: Optional[str], narrator: str) -> Dict[str, Any]:
    """Build ending credits section."""
    author_clause = f" by {author}" if author else ""

    script = DEFAULT_ENDING_CREDITS_TEMPLATE.format(
        title=title,
        author_clause=author_clause,
        narrator=narrator
    )

    return {
        "status": "generated",
        "script": script,
        "section_id": "ending_credits",
        "section_type": "credits"
    }


def _build_front_matter(front_matter: Dict[str, Any]) -> tuple:
    """
    Build front matter sections from parsed manuscript.

    Returns:
        (sections_list, missing_list)
    """
    sections = []
    missing = []

    # Define front matter types in order
    front_matter_types = [
        ("dedication", "Dedication"),
        ("foreword", "Foreword"),
        ("preface", "Preface"),
        ("introduction", "Introduction"),
        ("prologue", "Prologue"),
    ]

    for fm_id, fm_name in front_matter_types:
        text = front_matter.get(fm_id)
        if text and text.strip():
            sections.append({
                "id": fm_id,
                "name": fm_name,
                "status": "present",
                "text": text.strip(),
                "section_id": f"front_matter_{fm_id}",
                "section_type": "front_matter"
            })
        else:
            missing.append(fm_id)

    # Handle "other" front matter
    other = front_matter.get("other", [])
    if other and isinstance(other, list):
        for i, item in enumerate(other):
            if item and isinstance(item, str) and item.strip():
                sections.append({
                    "id": f"other_{i+1}",
                    "name": f"Front Matter {i+1}",
                    "status": "present",
                    "text": item.strip(),
                    "section_id": f"front_matter_other_{i+1}",
                    "section_type": "front_matter"
                })

    return sections, missing


def _build_body_matter(chapters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Build body/chapter sections."""
    body = []

    for chapter in chapters:
        text = chapter.get("text", "")
        if not text or not text.strip():
            continue

        index = chapter.get("index", len(body) + 1)
        title = chapter.get("title", f"Chapter {index}")

        body.append({
            "index": index,
            "title": title,
            "text": text.strip(),
            "section_id": f"chapter_{index:02d}",
            "section_type": "chapter",
            "word_count": len(text.split())
        })

    # Sort by index
    body.sort(key=lambda x: x.get("index", 0))

    return body


def _build_back_matter(back_matter: Dict[str, Any]) -> tuple:
    """
    Build back matter sections from parsed manuscript.

    Returns:
        (sections_list, missing_list)
    """
    sections = []
    missing = []

    # Define back matter types in order
    back_matter_types = [
        ("epilogue", "Epilogue"),
        ("afterword", "Afterword"),
        ("acknowledgements", "Acknowledgements"),
        ("about_author", "About the Author"),
    ]

    for bm_id, bm_name in back_matter_types:
        text = back_matter.get(bm_id)
        if text and text.strip():
            sections.append({
                "id": bm_id,
                "name": bm_name,
                "status": "present",
                "text": text.strip(),
                "section_id": f"back_matter_{bm_id}",
                "section_type": "back_matter"
            })
        else:
            missing.append(bm_id)

    # Handle "other" back matter
    other = back_matter.get("other", [])
    if other and isinstance(other, list):
        for i, item in enumerate(other):
            if item and isinstance(item, str) and item.strip():
                sections.append({
                    "id": f"other_{i+1}",
                    "name": f"Back Matter {i+1}",
                    "status": "present",
                    "text": item.strip(),
                    "section_id": f"back_matter_other_{i+1}",
                    "section_type": "back_matter"
                })

    return sections, missing


def _format_retail_sample(retail_sample: Dict[str, Any]) -> Dict[str, Any]:
    """Format retail sample for the section plan."""
    return {
        "chapter_index": retail_sample.get("chapter_index", 1),
        "chapter_title": retail_sample.get("chapter_title"),
        "text": retail_sample.get("excerpt_text", ""),
        "approx_word_count": retail_sample.get("approx_word_count", 0),
        "approx_duration_seconds": retail_sample.get("approx_duration_seconds", 0),
        "reason": retail_sample.get("reason", ""),
        "section_id": "retail_sample",
        "section_type": "sample"
    }


def _count_total_sections(
    opening: Dict,
    front: List,
    body: List,
    back: List,
    ending: Dict
) -> int:
    """Count total number of sections to produce."""
    count = 2  # Opening + Ending credits
    count += len(front)
    count += len(body)
    count += len(back)
    count += 1  # Retail sample
    return count


def get_section_order(plan: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Get all sections in production order.

    Args:
        plan: Full section plan

    Returns:
        List of sections in order they should be produced
    """
    sections = []

    # 1. Opening credits
    sections.append(plan["opening_credits"])

    # 2. Front matter
    sections.extend(plan["front_matter"])

    # 3. Body (chapters)
    sections.extend(plan["body_matter"])

    # 4. Back matter
    sections.extend(plan["back_matter"])

    # 5. Ending credits
    sections.append(plan["ending_credits"])

    # Retail sample is separate (not part of main audiobook flow)

    return sections


def get_sections_for_tts(plan: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Get all sections that need TTS generation.

    Args:
        plan: Full section plan

    Returns:
        List of sections with text that needs TTS
    """
    sections = get_section_order(plan)

    # Add retail sample
    sections.append(plan["retail_sample"])

    # Filter to only those with text
    return [s for s in sections if s.get("text") or s.get("script")]


def estimate_total_duration(plan: Dict[str, Any], words_per_minute: int = 150) -> int:
    """
    Estimate total audiobook duration in seconds.

    Args:
        plan: Section plan
        words_per_minute: Narration speed (default 150)

    Returns:
        Estimated duration in seconds
    """
    total_words = 0

    # Count words in all sections
    for section in get_section_order(plan):
        text = section.get("text") or section.get("script", "")
        total_words += len(text.split())

    # Calculate duration
    duration_minutes = total_words / words_per_minute
    duration_seconds = int(duration_minutes * 60)

    return duration_seconds
