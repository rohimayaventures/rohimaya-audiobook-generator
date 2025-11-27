"""
Manuscript Parser Agent

Uses OpenAI to analyze manuscript structure and extract:
- Title and author (if present)
- Front matter (dedication, foreword, etc.)
- Chapters with titles
- Back matter (afterword, acknowledgements, about author, etc.)

This provides richer structure than simple regex-based chapter parsing.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)

# System prompt for manuscript analysis
PARSER_SYSTEM_PROMPT = """You are an expert book editor and manuscript analyzer. Your task is to analyze a manuscript and extract its structure.

Analyze the provided manuscript text and return a JSON object with the following structure:

{
  "title": "Book Title" or null if not found,
  "author": "Author Name" or null if not found,
  "front_matter": {
    "dedication": "Dedication text" or null,
    "foreword": "Foreword text" or null,
    "preface": "Preface text" or null,
    "introduction": "Introduction text" or null,
    "prologue": "Prologue text" or null,
    "other": ["Any other front matter sections"]
  },
  "chapters": [
    {
      "index": 1,
      "title": "Chapter Title" or "Chapter 1" if no title,
      "text": "Full chapter text content"
    }
  ],
  "back_matter": {
    "epilogue": "Epilogue text" or null,
    "afterword": "Afterword text" or null,
    "acknowledgements": "Acknowledgements text" or null,
    "about_author": "About the Author text" or null,
    "other": ["Any other back matter sections"]
  }
}

Rules:
1. Extract the actual text content for each section, not just labels.
2. If no chapters are explicitly marked, treat logical breaks as chapters, or the entire text as Chapter 1.
3. Look for common patterns: "Chapter 1", "CHAPTER ONE", "Part 1", section breaks, etc.
4. Front matter comes before the main story. Back matter comes after.
5. Preserve the original text as much as possible, including paragraph breaks.
6. If title/author aren't explicitly in the manuscript, leave them null.
7. Always return valid JSON.
"""


def parse_manuscript_structure(
    manuscript_text: str,
    api_key: str,
    max_tokens: int = 16000,
    model: str = "gpt-4o-mini"
) -> Dict[str, Any]:
    """
    Use OpenAI to analyze the manuscript and return a structured map.

    Args:
        manuscript_text: Full manuscript text
        api_key: OpenAI API key
        max_tokens: Maximum tokens for the response
        model: OpenAI model to use

    Returns:
        Dictionary with structure:
        {
            "title": str | None,
            "author": str | None,
            "front_matter": {
                "dedication": str | None,
                "foreword": str | None,
                "preface": str | None,
                "introduction": str | None,
                "prologue": str | None,
                "other": [str]
            },
            "chapters": [
                { "index": int, "title": str | None, "text": str },
                ...
            ],
            "back_matter": {
                "epilogue": str | None,
                "afterword": str | None,
                "acknowledgements": str | None,
                "about_author": str | None,
                "other": [str]
            }
        }
    """
    logger.info(f"Parsing manuscript structure ({len(manuscript_text)} chars)")

    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)

    # Truncate very long manuscripts to fit in context
    # Keep first and last portions to capture front/back matter
    max_input_chars = 100000  # ~25k tokens
    if len(manuscript_text) > max_input_chars:
        logger.warning(f"Manuscript too long ({len(manuscript_text)} chars), truncating for analysis")
        # Keep more from beginning (front matter + early chapters)
        # and some from end (back matter)
        front_portion = manuscript_text[:int(max_input_chars * 0.7)]
        back_portion = manuscript_text[-int(max_input_chars * 0.3):]
        manuscript_text = front_portion + "\n\n[... CONTENT TRUNCATED FOR ANALYSIS ...]\n\n" + back_portion

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": PARSER_SYSTEM_PROMPT},
                {"role": "user", "content": f"Please analyze this manuscript and extract its structure:\n\n{manuscript_text}"}
            ],
            max_tokens=max_tokens,
            temperature=0.1,  # Low temperature for consistent structure
            response_format={"type": "json_object"}
        )

        # Parse the response
        result_text = response.choices[0].message.content
        result = json.loads(result_text)

        # Validate and ensure all expected fields exist
        result = _ensure_structure(result)

        logger.info(f"Parsed manuscript: {len(result.get('chapters', []))} chapters found")
        return result

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse OpenAI response as JSON: {e}")
        return _create_fallback_structure(manuscript_text)

    except Exception as e:
        logger.error(f"Error parsing manuscript with OpenAI: {e}")
        return _create_fallback_structure(manuscript_text)


def _ensure_structure(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure the result has all expected fields with proper defaults.

    Args:
        result: Raw parsed result from OpenAI

    Returns:
        Result with all fields guaranteed to exist
    """
    # Ensure top-level fields
    result.setdefault("title", None)
    result.setdefault("author", None)

    # Ensure front_matter
    front_matter = result.get("front_matter", {})
    if not isinstance(front_matter, dict):
        front_matter = {}
    front_matter.setdefault("dedication", None)
    front_matter.setdefault("foreword", None)
    front_matter.setdefault("preface", None)
    front_matter.setdefault("introduction", None)
    front_matter.setdefault("prologue", None)
    front_matter.setdefault("other", [])
    result["front_matter"] = front_matter

    # Ensure chapters
    chapters = result.get("chapters", [])
    if not isinstance(chapters, list):
        chapters = []

    # Validate each chapter
    valid_chapters = []
    for i, chapter in enumerate(chapters):
        if isinstance(chapter, dict) and chapter.get("text"):
            chapter.setdefault("index", i + 1)
            chapter.setdefault("title", f"Chapter {chapter['index']}")
            valid_chapters.append(chapter)
    result["chapters"] = valid_chapters

    # Ensure back_matter
    back_matter = result.get("back_matter", {})
    if not isinstance(back_matter, dict):
        back_matter = {}
    back_matter.setdefault("epilogue", None)
    back_matter.setdefault("afterword", None)
    back_matter.setdefault("acknowledgements", None)
    back_matter.setdefault("about_author", None)
    back_matter.setdefault("other", [])
    result["back_matter"] = back_matter

    return result


def _create_fallback_structure(manuscript_text: str) -> Dict[str, Any]:
    """
    Create a basic structure when OpenAI parsing fails.
    Falls back to treating the entire manuscript as a single chapter.

    Args:
        manuscript_text: Full manuscript text

    Returns:
        Basic structure with single chapter
    """
    logger.warning("Using fallback structure (single chapter)")

    return {
        "title": None,
        "author": None,
        "front_matter": {
            "dedication": None,
            "foreword": None,
            "preface": None,
            "introduction": None,
            "prologue": None,
            "other": []
        },
        "chapters": [
            {
                "index": 1,
                "title": "Chapter 1",
                "text": manuscript_text.strip()
            }
        ],
        "back_matter": {
            "epilogue": None,
            "afterword": None,
            "acknowledgements": None,
            "about_author": None,
            "other": []
        }
    }


def parse_manuscript_simple(manuscript_text: str) -> Dict[str, Any]:
    """
    Simple regex-based fallback parser that doesn't require API calls.
    Uses the existing chapter_parser module logic.

    Args:
        manuscript_text: Full manuscript text

    Returns:
        Basic structure compatible with the agent output
    """
    import re

    # Try to extract title from first few lines
    lines = manuscript_text.strip().split('\n')
    title = None
    author = None

    # Look for title/author patterns in first 10 lines
    for line in lines[:10]:
        line = line.strip()
        if not line:
            continue
        if not title and len(line) < 100 and not line.lower().startswith('chapter'):
            # First non-empty, reasonably short line might be title
            title = line
        elif title and not author and line.lower().startswith('by '):
            author = line[3:].strip()
            break

    # Use regex to find chapters
    chapter_regex = re.compile(
        r"^\s*(?:CHAPTER|Chapter|PART|Part)\s+(\d+|[IVXLCDM]+|One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten)\s*[:\-]?\s*(.*)$",
        re.MULTILINE | re.IGNORECASE
    )

    chapters = []
    matches = list(chapter_regex.finditer(manuscript_text))

    if matches:
        for i, match in enumerate(matches):
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(manuscript_text)

            chapter_num = match.group(1)
            # Convert roman numerals or words to numbers
            try:
                if chapter_num.isdigit():
                    index = int(chapter_num)
                else:
                    index = i + 1
            except:
                index = i + 1

            chapter_title = match.group(2).strip() or f"Chapter {index}"
            chapter_text = manuscript_text[start:end].strip()

            if chapter_text:
                chapters.append({
                    "index": index,
                    "title": chapter_title,
                    "text": chapter_text
                })
    else:
        # No chapters found, treat entire text as single chapter
        chapters = [{
            "index": 1,
            "title": title or "Chapter 1",
            "text": manuscript_text.strip()
        }]

    return {
        "title": title,
        "author": author,
        "front_matter": {
            "dedication": None,
            "foreword": None,
            "preface": None,
            "introduction": None,
            "prologue": None,
            "other": []
        },
        "chapters": chapters,
        "back_matter": {
            "epilogue": None,
            "afterword": None,
            "acknowledgements": None,
            "about_author": None,
            "other": []
        }
    }
