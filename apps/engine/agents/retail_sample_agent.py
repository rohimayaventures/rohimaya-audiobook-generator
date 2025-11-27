"""
Retail Sample Selector Agent

Uses OpenAI to intelligently select an engaging excerpt from the book
that works well as a retail sample (the preview listeners hear before buying).

The agent selects:
- An excerpt from early chapters (usually 1-3)
- A compelling, self-contained scene
- Target duration of 1-5 minutes (based on word count)
- Optionally biased toward "spicy" content for romance novels
"""

import json
import logging
from typing import Dict, Any, List, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)

# System prompt for retail sample selection
SAMPLE_SELECTOR_PROMPT = """You are an expert audiobook marketing specialist. Your task is to select the perfect excerpt from a book to use as the retail sample - the preview that potential listeners hear before purchasing.

A great retail sample should:
1. Hook the listener immediately with compelling content
2. Be self-contained enough to understand without context
3. Showcase the author's writing style and voice
4. Leave the listener wanting more
5. Come from early chapters (usually 1-3) so it doesn't spoil the plot
6. Be approximately 500-800 words for a ~3-5 minute sample

Based on the manuscript structure provided, select the best excerpt and return a JSON object:

{
  "chapter_index": 1,
  "chapter_title": "Chapter title",
  "excerpt_text": "The full text of the selected excerpt...",
  "start_marker": "First few words of the excerpt for location reference",
  "end_marker": "Last few words of the excerpt",
  "approx_word_count": 650,
  "approx_duration_seconds": 260,
  "reason": "Brief explanation of why this excerpt was chosen"
}

Rules:
1. The excerpt_text must be EXACT text from the manuscript - do not modify or paraphrase
2. Target word count: 500-800 words (3-5 minutes at ~150 wpm)
3. Select from chapters 1-3 only
4. Choose a scene with action, dialogue, or emotional tension
5. Avoid scenes that require too much context to understand
6. The excerpt should have a mini arc - beginning, tension, and partial resolution
"""

SPICY_PROMPT_ADDITION = """
SPECIAL INSTRUCTION: This is a romance novel and the publisher wants a "spicy" sample that showcases the romantic tension or chemistry. Select an excerpt that:
- Features romantic tension, chemistry, or intimate moments
- Highlights the connection between main characters
- Is still appropriate for a retail preview (not explicit)
- Creates anticipation for the romantic storyline
"""


def select_retail_sample_excerpt(
    manuscript_structure: Dict[str, Any],
    api_key: str,
    target_duration_minutes: float = 4.0,
    average_words_per_minute: int = 150,
    preferred_style: str = "default",  # "default" | "spicy"
    model: str = "gpt-4o-mini"
) -> Dict[str, Any]:
    """
    Select a retail sample excerpt from the manuscript.

    Args:
        manuscript_structure: Parsed manuscript from manuscript_parser_agent
        api_key: OpenAI API key
        target_duration_minutes: Target length in minutes (default 4)
        average_words_per_minute: Reading speed assumption (default 150)
        preferred_style: "default" or "spicy" for romance novels
        model: OpenAI model to use

    Returns:
        Dictionary with:
        {
            "chapter_index": int,
            "chapter_title": str | None,
            "excerpt_text": str,
            "start_marker": str,
            "end_marker": str,
            "approx_word_count": int,
            "approx_duration_seconds": int,
            "reason": str
        }
    """
    target_words = int(target_duration_minutes * average_words_per_minute)
    logger.info(f"Selecting retail sample: target {target_words} words (~{target_duration_minutes} min)")

    # Get early chapters (1-3) for sample selection
    chapters = manuscript_structure.get("chapters", [])
    if not chapters:
        logger.warning("No chapters found in manuscript structure")
        return _create_fallback_sample(manuscript_structure, target_words)

    # Get first 3 chapters
    early_chapters = [c for c in chapters if c.get("index", 0) <= 3]
    if not early_chapters:
        early_chapters = chapters[:3]

    if not early_chapters:
        logger.warning("Could not find early chapters")
        return _create_fallback_sample(manuscript_structure, target_words)

    # Build context for OpenAI
    chapters_text = ""
    for chapter in early_chapters:
        # Truncate long chapters for context
        text = chapter.get("text", "")[:20000]  # ~5k tokens per chapter
        chapters_text += f"\n\n=== CHAPTER {chapter.get('index', '?')}: {chapter.get('title', 'Untitled')} ===\n\n{text}"

    # Build prompt
    system_prompt = SAMPLE_SELECTOR_PROMPT
    if preferred_style == "spicy":
        system_prompt += SPICY_PROMPT_ADDITION

    client = OpenAI(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Select the best retail sample excerpt from these early chapters. Target word count: {target_words} words (~{target_duration_minutes} minutes).\n\nManuscript chapters:{chapters_text}"
                }
            ],
            max_tokens=4000,
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        result_text = response.choices[0].message.content
        result = json.loads(result_text)

        # Validate result
        result = _validate_sample_result(result, early_chapters, target_words)

        logger.info(f"Selected retail sample from Chapter {result.get('chapter_index')}: {result.get('approx_word_count')} words")
        return result

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse OpenAI response as JSON: {e}")
        return _create_fallback_sample(manuscript_structure, target_words)

    except Exception as e:
        logger.error(f"Error selecting retail sample: {e}")
        return _create_fallback_sample(manuscript_structure, target_words)


def _validate_sample_result(
    result: Dict[str, Any],
    early_chapters: List[Dict[str, Any]],
    target_words: int
) -> Dict[str, Any]:
    """
    Validate and fix the sample selection result.

    Args:
        result: Raw result from OpenAI
        early_chapters: List of early chapter dicts
        target_words: Target word count

    Returns:
        Validated result with all fields
    """
    # Ensure all required fields exist
    result.setdefault("chapter_index", 1)
    result.setdefault("chapter_title", None)
    result.setdefault("excerpt_text", "")
    result.setdefault("start_marker", "")
    result.setdefault("end_marker", "")
    result.setdefault("reason", "Selected as representative excerpt from early chapters")

    # Calculate word count and duration if not provided
    excerpt_text = result.get("excerpt_text", "")
    word_count = len(excerpt_text.split())
    result["approx_word_count"] = word_count
    result["approx_duration_seconds"] = int(word_count / 150 * 60)

    # Validate excerpt exists and isn't too short
    if word_count < 100:
        logger.warning("Excerpt too short, using fallback")
        # Find the chapter and use first portion
        chapter_index = result.get("chapter_index", 1)
        for chapter in early_chapters:
            if chapter.get("index") == chapter_index:
                text = chapter.get("text", "")
                # Extract approximately target_words
                words = text.split()
                excerpt_words = words[:target_words]
                result["excerpt_text"] = " ".join(excerpt_words)
                result["approx_word_count"] = len(excerpt_words)
                result["approx_duration_seconds"] = int(len(excerpt_words) / 150 * 60)
                result["reason"] = "Fallback: First portion of chapter"
                break

    return result


def _create_fallback_sample(
    manuscript_structure: Dict[str, Any],
    target_words: int
) -> Dict[str, Any]:
    """
    Create a fallback sample from the first chapter.

    Args:
        manuscript_structure: Parsed manuscript
        target_words: Target word count

    Returns:
        Fallback sample dict
    """
    logger.info("Creating fallback retail sample from Chapter 1")

    chapters = manuscript_structure.get("chapters", [])
    if not chapters:
        # No chapters at all - this shouldn't happen but handle it
        return {
            "chapter_index": 1,
            "chapter_title": "Chapter 1",
            "excerpt_text": "No content available for sample.",
            "start_marker": "",
            "end_marker": "",
            "approx_word_count": 0,
            "approx_duration_seconds": 0,
            "reason": "Fallback: No chapters available"
        }

    # Get first chapter
    first_chapter = chapters[0]
    text = first_chapter.get("text", "")

    # Extract target_words from the beginning
    words = text.split()
    excerpt_words = words[:target_words]
    excerpt_text = " ".join(excerpt_words)

    # Find a good sentence ending within the excerpt
    # Look for sentence-ending punctuation
    last_period = excerpt_text.rfind('.')
    last_exclaim = excerpt_text.rfind('!')
    last_question = excerpt_text.rfind('?')
    last_quote = excerpt_text.rfind('"')

    # Find the last sentence boundary
    boundaries = [b for b in [last_period, last_exclaim, last_question] if b > len(excerpt_text) * 0.7]
    if boundaries:
        best_boundary = max(boundaries)
        # Check if there's a closing quote right after
        if last_quote > best_boundary and last_quote - best_boundary < 3:
            best_boundary = last_quote
        excerpt_text = excerpt_text[:best_boundary + 1]

    final_word_count = len(excerpt_text.split())

    return {
        "chapter_index": first_chapter.get("index", 1),
        "chapter_title": first_chapter.get("title"),
        "excerpt_text": excerpt_text.strip(),
        "start_marker": " ".join(excerpt_text.split()[:5]),
        "end_marker": " ".join(excerpt_text.split()[-5:]),
        "approx_word_count": final_word_count,
        "approx_duration_seconds": int(final_word_count / 150 * 60),
        "reason": "Fallback: Opening excerpt from Chapter 1"
    }
