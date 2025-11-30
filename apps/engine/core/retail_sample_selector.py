"""
Retail Sample Selector - AI-powered "spicy" excerpt selection

Uses Gemini AI to analyze the first 3 chapters and select the most engaging
excerpt for the retail sample. The algorithm prioritizes:

1. HIGH engagement (action, dialogue, emotional moments)
2. HIGH emotional intensity (drama, tension, romance)
3. LOW spoiler risk (no major plot reveals)

Target duration: 3-5 minutes (~450-750 words at 150 wpm)
"""

import logging
import json
import re
from typing import List, Dict, Optional, Tuple
import os

logger = logging.getLogger(__name__)

# Try to import google.generativeai (optional dependency)
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    GENAI_AVAILABLE = False
    logger.warning("google-generativeai not installed - AI retail sample selection disabled")

# Target word count for retail sample (3-5 minutes at 150 wpm)
MIN_SAMPLE_WORDS = 400
MAX_SAMPLE_WORDS = 800
TARGET_SAMPLE_WORDS = 600

# Configure Gemini (try multiple env var names for compatibility)
GEMINI_API_KEY = os.getenv("GOOGLE_GENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY and GENAI_AVAILABLE:
    genai.configure(api_key=GEMINI_API_KEY)
    logger.info("Gemini AI configured for retail sample selection")


SAMPLE_ANALYSIS_PROMPT = """You are an expert audiobook producer selecting the perfect retail sample excerpt.

A retail sample is the 3-5 minute preview that potential listeners hear before purchasing. It must:
- HOOK the listener immediately with engaging content
- SHOWCASE the author's writing style and voice
- AVOID major plot spoilers
- WORK as standalone content (doesn't require context)

Analyze the following chapters (FIRST 3 CHAPTERS ONLY) and identify the BEST excerpt for a retail sample.

SCORING CRITERIA (0.0 to 1.0 scale):
1. ENGAGEMENT (0.0-1.0): Action, dialogue, tension, humor, romance - anything that hooks listeners
2. EMOTIONAL_INTENSITY (0.0-1.0): How emotionally compelling is the passage?
3. SPOILER_RISK (0.0-1.0): 0.0 = no spoilers (good), 1.0 = major spoilers (bad)

The IDEAL excerpt has:
- Engagement >= 0.7
- Emotional intensity >= 0.6
- Spoiler risk <= 0.3

TARGET LENGTH: 450-750 words (approximately 3-5 minutes of audio)

CHAPTERS TO ANALYZE:
{chapters_text}

Respond with a JSON object containing your TOP 3 candidate excerpts:
{{
    "candidates": [
        {{
            "chapter_index": <0-based chapter index>,
            "chapter_title": "<chapter title>",
            "start_sentence": "<first sentence of excerpt - use exact text>",
            "end_sentence": "<last sentence of excerpt - use exact text>",
            "word_count": <approximate word count>,
            "engagement_score": <0.0-1.0>,
            "emotional_intensity_score": <0.0-1.0>,
            "spoiler_risk_score": <0.0-1.0>,
            "overall_score": <calculated: (engagement + emotional) / 2 - spoiler_risk>,
            "reason": "<brief explanation of why this excerpt works>"
        }}
    ],
    "recommendation": {{
        "selected_index": <index in candidates array (0, 1, or 2)>,
        "confidence": <0.0-1.0>,
        "explanation": "<why this is the best choice>"
    }}
}}

IMPORTANT: The excerpt text is identified by start_sentence and end_sentence. Use EXACT text from the chapters so we can locate the excerpt programmatically.
"""


def select_retail_sample(
    chapters: List[Dict],
    max_chapters_to_analyze: int = 3,
    use_ai: bool = True,
) -> Dict:
    """
    Select the best retail sample excerpt from the first few chapters.

    Args:
        chapters: List of chapter dicts with 'text', 'title', 'chapter_index'
        max_chapters_to_analyze: How many chapters to analyze (default 3)
        use_ai: Whether to use Gemini AI for selection (default True)

    Returns:
        Dict with:
        {
            "chapter_index": int,
            "chapter_title": str,
            "excerpt_text": str,
            "word_count": int,
            "engagement_score": float,
            "emotional_intensity_score": float,
            "spoiler_risk_score": float,
            "overall_score": float,
            "reason": str,
            "is_ai_selected": bool,
            "candidates": List[Dict],  # All candidates considered
        }
    """
    if not chapters:
        logger.warning("No chapters provided for retail sample selection")
        return _create_fallback_sample(chapters)

    # Get body chapters only (skip front matter)
    body_chapters = [
        ch for ch in chapters
        if ch.get("segment_type", "body_chapter") == "body_chapter"
    ]

    if not body_chapters:
        body_chapters = chapters  # Fallback to all chapters

    # Limit to first N chapters
    chapters_to_analyze = body_chapters[:max_chapters_to_analyze]

    if use_ai and GEMINI_API_KEY and GENAI_AVAILABLE:
        try:
            return _select_with_gemini(chapters_to_analyze)
        except Exception as e:
            logger.error(f"Gemini sample selection failed: {e}")
            logger.info("Falling back to heuristic selection")

    # Fallback to heuristic selection
    return _select_with_heuristics(chapters_to_analyze)


def _select_with_gemini(chapters: List[Dict]) -> Dict:
    """Use Gemini AI to select the best retail sample."""
    logger.info(f"Using Gemini AI to analyze {len(chapters)} chapters for retail sample")

    # Format chapters for the prompt
    chapters_text = ""
    for i, ch in enumerate(chapters):
        title = ch.get("title", f"Chapter {i + 1}")
        text = ch.get("text", "")[:15000]  # Limit text to avoid token limits
        chapters_text += f"\n\n=== CHAPTER {i} - {title} ===\n{text}"

    # Call Gemini
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = SAMPLE_ANALYSIS_PROMPT.format(chapters_text=chapters_text)

    response = model.generate_content(prompt)
    response_text = response.text

    # Parse JSON response
    try:
        # Extract JSON from response (handle markdown code blocks)
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            result = json.loads(json_match.group())
        else:
            raise ValueError("No JSON found in response")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini response: {e}")
        logger.debug(f"Response was: {response_text[:500]}")
        return _select_with_heuristics(chapters)

    # Extract the recommended candidate
    candidates = result.get("candidates", [])
    if not candidates:
        return _select_with_heuristics(chapters)

    recommendation = result.get("recommendation", {})
    selected_idx = recommendation.get("selected_index", 0)

    if selected_idx >= len(candidates):
        selected_idx = 0

    selected = candidates[selected_idx]

    # Find and extract the actual excerpt text
    chapter_idx = selected.get("chapter_index", 0)
    if chapter_idx >= len(chapters):
        chapter_idx = 0

    chapter_text = chapters[chapter_idx].get("text", "")
    excerpt_text = _extract_excerpt_by_sentences(
        chapter_text,
        selected.get("start_sentence", ""),
        selected.get("end_sentence", ""),
        target_words=TARGET_SAMPLE_WORDS
    )

    # If extraction failed, use heuristic fallback for this chapter
    if not excerpt_text or len(excerpt_text.split()) < MIN_SAMPLE_WORDS:
        excerpt_text = _extract_engaging_excerpt(chapter_text)

    return {
        "chapter_index": chapter_idx,
        "chapter_title": chapters[chapter_idx].get("title", f"Chapter {chapter_idx + 1}"),
        "excerpt_text": excerpt_text,
        "word_count": len(excerpt_text.split()),
        "engagement_score": selected.get("engagement_score", 0.5),
        "emotional_intensity_score": selected.get("emotional_intensity_score", 0.5),
        "spoiler_risk_score": selected.get("spoiler_risk_score", 0.3),
        "overall_score": selected.get("overall_score", 0.5),
        "reason": selected.get("reason", "AI-selected engaging excerpt"),
        "is_ai_selected": True,
        "candidates": candidates,
        "ai_confidence": recommendation.get("confidence", 0.7),
        "ai_explanation": recommendation.get("explanation", ""),
    }


def _select_with_heuristics(chapters: List[Dict]) -> Dict:
    """Fallback heuristic-based selection when AI is unavailable."""
    logger.info("Using heuristic-based retail sample selection")

    best_excerpt = None
    best_score = -1

    for i, ch in enumerate(chapters):
        text = ch.get("text", "")
        if not text:
            continue

        # Score based on dialogue density and paragraph variety
        excerpt = _extract_engaging_excerpt(text)
        score = _score_excerpt(excerpt)

        if score > best_score:
            best_score = score
            best_excerpt = {
                "chapter_index": ch.get("chapter_index", i),
                "chapter_title": ch.get("title", f"Chapter {i + 1}"),
                "excerpt_text": excerpt,
                "word_count": len(excerpt.split()),
                "engagement_score": min(score, 1.0),
                "emotional_intensity_score": 0.5,
                "spoiler_risk_score": 0.2 if i == 0 else 0.3,  # First chapter is safer
                "overall_score": score * 0.8,  # Penalize heuristic selection slightly
                "reason": "Heuristic selection based on dialogue and paragraph density",
                "is_ai_selected": False,
                "candidates": [],
            }

    if not best_excerpt:
        return _create_fallback_sample(chapters)

    return best_excerpt


def _extract_excerpt_by_sentences(
    text: str,
    start_sentence: str,
    end_sentence: str,
    target_words: int = TARGET_SAMPLE_WORDS
) -> str:
    """Extract excerpt between start and end sentences."""
    if not start_sentence or not end_sentence:
        return ""

    # Clean up the sentences for matching
    start_clean = start_sentence.strip()[:100]  # First 100 chars
    end_clean = end_sentence.strip()[:100]

    # Find positions
    start_pos = text.find(start_clean[:50])  # Use first 50 chars for matching
    if start_pos == -1:
        # Try fuzzy matching
        start_pos = _fuzzy_find(text, start_clean)

    if start_pos == -1:
        return ""

    end_pos = text.find(end_clean[:50], start_pos)
    if end_pos == -1:
        end_pos = _fuzzy_find(text, end_clean, start_pos)

    if end_pos == -1:
        # Just take target_words from start_pos
        words = text[start_pos:].split()
        return " ".join(words[:target_words])

    # Extract and clean
    excerpt = text[start_pos:end_pos + len(end_sentence)]
    return excerpt.strip()


def _fuzzy_find(text: str, needle: str, start: int = 0) -> int:
    """Fuzzy string matching - find approximate position."""
    # Simple approach: look for first few words
    words = needle.split()[:5]
    if not words:
        return -1

    search_text = " ".join(words)
    return text.find(search_text, start)


def _extract_engaging_excerpt(text: str, target_words: int = TARGET_SAMPLE_WORDS) -> str:
    """
    Extract the most engaging excerpt from text using heuristics.

    Looks for:
    - Dialogue-heavy sections (quotes)
    - Action sequences
    - Scene openings
    """
    paragraphs = text.split('\n\n')
    if not paragraphs:
        return text[:3000]

    # Score each paragraph
    scored_paragraphs = []
    for i, para in enumerate(paragraphs):
        if len(para.strip()) < 50:
            continue

        score = 0
        # Dialogue bonus
        quote_count = para.count('"') + para.count("'")
        score += min(quote_count * 0.1, 0.5)

        # Action words bonus
        action_words = ['ran', 'jumped', 'grabbed', 'shouted', 'whispered', 'slammed',
                        'rushed', 'fought', 'kissed', 'cried', 'laughed', 'screamed']
        for word in action_words:
            if word in para.lower():
                score += 0.1

        # Not too early (skip intro exposition)
        if i > 2:
            score += 0.1

        scored_paragraphs.append((i, para, score))

    # Sort by score
    scored_paragraphs.sort(key=lambda x: x[2], reverse=True)

    if not scored_paragraphs:
        return text[:3000]

    # Start with best paragraph and expand
    best_idx = scored_paragraphs[0][0]
    result_paragraphs = [paragraphs[best_idx]]
    word_count = len(paragraphs[best_idx].split())

    # Add surrounding paragraphs until we hit target
    offset = 1
    while word_count < target_words:
        added = False

        # Add paragraph before
        if best_idx - offset >= 0:
            para = paragraphs[best_idx - offset]
            result_paragraphs.insert(0, para)
            word_count += len(para.split())
            added = True

        # Add paragraph after
        if best_idx + offset < len(paragraphs) and word_count < target_words:
            para = paragraphs[best_idx + offset]
            result_paragraphs.append(para)
            word_count += len(para.split())
            added = True

        offset += 1
        if not added or offset > 20:
            break

    # Trim to target if too long
    result = "\n\n".join(result_paragraphs)
    words = result.split()
    if len(words) > MAX_SAMPLE_WORDS:
        result = " ".join(words[:MAX_SAMPLE_WORDS])
        # Try to end at sentence boundary
        last_period = result.rfind('.')
        if last_period > len(result) * 0.7:
            result = result[:last_period + 1]

    return result.strip()


def _score_excerpt(text: str) -> float:
    """Score an excerpt for engagement (0.0 - 1.0)."""
    if not text:
        return 0.0

    score = 0.5  # Base score

    # Dialogue density (quotes)
    quote_ratio = (text.count('"') + text.count("'")) / max(len(text), 1) * 100
    score += min(quote_ratio * 0.5, 0.2)

    # Paragraph variety
    paragraphs = text.split('\n\n')
    if len(paragraphs) >= 3:
        score += 0.1

    # Word count in range
    word_count = len(text.split())
    if MIN_SAMPLE_WORDS <= word_count <= MAX_SAMPLE_WORDS:
        score += 0.1
    elif word_count < MIN_SAMPLE_WORDS * 0.5:
        score -= 0.2

    # Action/emotion words
    engaging_words = ['suddenly', 'heart', 'breath', 'eyes', 'voice', 'moment',
                      'felt', 'knew', 'wanted', 'need', 'love', 'fear']
    for word in engaging_words:
        if word in text.lower():
            score += 0.02

    return min(max(score, 0.0), 1.0)


def _create_fallback_sample(chapters: List[Dict]) -> Dict:
    """Create a fallback sample when all else fails."""
    if not chapters:
        return {
            "chapter_index": 0,
            "chapter_title": "Chapter 1",
            "excerpt_text": "",
            "word_count": 0,
            "engagement_score": 0.0,
            "emotional_intensity_score": 0.0,
            "spoiler_risk_score": 0.0,
            "overall_score": 0.0,
            "reason": "No chapters available for sample selection",
            "is_ai_selected": False,
            "candidates": [],
        }

    # Use start of first chapter
    first_chapter = chapters[0]
    text = first_chapter.get("text", "")
    words = text.split()[:TARGET_SAMPLE_WORDS]
    excerpt = " ".join(words)

    # Try to end at sentence boundary
    last_period = excerpt.rfind('.')
    if last_period > len(excerpt) * 0.7:
        excerpt = excerpt[:last_period + 1]

    return {
        "chapter_index": first_chapter.get("chapter_index", 0),
        "chapter_title": first_chapter.get("title", "Chapter 1"),
        "excerpt_text": excerpt,
        "word_count": len(excerpt.split()),
        "engagement_score": 0.4,
        "emotional_intensity_score": 0.4,
        "spoiler_risk_score": 0.2,
        "overall_score": 0.4,
        "reason": "Fallback selection: beginning of first chapter",
        "is_ai_selected": False,
        "candidates": [],
    }


def format_sample_for_db(sample: Dict, job_id: str, source_chapter_id: Optional[str] = None) -> Dict:
    """
    Format a retail sample selection for database insertion.

    Args:
        sample: Sample dict from select_retail_sample()
        job_id: UUID of the job
        source_chapter_id: UUID of the source chapter (optional)

    Returns:
        Dict ready for insertion into retail_samples table
    """
    return {
        "job_id": job_id,
        "source_chapter_id": source_chapter_id,
        "source_chapter_title": sample.get("chapter_title"),
        "sample_text": sample.get("excerpt_text", ""),
        "word_count": sample.get("word_count", 0),
        "character_count": len(sample.get("excerpt_text", "")),
        "estimated_duration_seconds": int(sample.get("word_count", 0) / 150 * 60),
        "engagement_score": sample.get("engagement_score"),
        "emotional_intensity_score": sample.get("emotional_intensity_score"),
        "spoiler_risk_score": sample.get("spoiler_risk_score"),
        "overall_score": sample.get("overall_score"),
        "is_auto_suggested": True,
        "is_user_confirmed": False,
        "is_final": False,
    }
