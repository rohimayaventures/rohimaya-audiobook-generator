"""
Chapter Parser - Extract and parse chapters from book text
Enhanced version with multi-format detection and deterministic ordering

Supports:
- CHAPTER 1, Chapter One, CHAPTER I (Roman numerals)
- Part I, Part 1, Part One
- Prologue, Epilogue, Afterword, etc.
- Section breaks (*** or ---)
- Numbered sections without "Chapter" prefix
"""

import re
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


# Chapter header patterns (order matters - more specific first)
CHAPTER_PATTERNS = [
    # Explicit "Chapter" with number
    (r"^\s*CHAPTER\s+(\d+)\s*[:\.\-]?\s*(.*)$", "chapter_num"),
    (r"^\s*Chapter\s+(\d+)\s*[:\.\-]?\s*(.*)$", "chapter_num"),

    # "Chapter" with word number (One, Two, etc.)
    (r"^\s*CHAPTER\s+(ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN|ELEVEN|TWELVE|THIRTEEN|FOURTEEN|FIFTEEN|SIXTEEN|SEVENTEEN|EIGHTEEN|NINETEEN|TWENTY)\s*[:\.\-]?\s*(.*)$", "chapter_word"),
    (r"^\s*Chapter\s+(One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|Eleven|Twelve|Thirteen|Fourteen|Fifteen|Sixteen|Seventeen|Eighteen|Nineteen|Twenty)\s*[:\.\-]?\s*(.*)$", "chapter_word"),

    # Roman numerals (I, II, III, IV, V, etc.)
    (r"^\s*CHAPTER\s+([IVXLC]+)\s*[:\.\-]?\s*(.*)$", "chapter_roman"),
    (r"^\s*Chapter\s+([IVXLCivxlc]+)\s*[:\.\-]?\s*(.*)$", "chapter_roman"),

    # Part headers
    (r"^\s*PART\s+(\d+)\s*[:\.\-]?\s*(.*)$", "part_num"),
    (r"^\s*Part\s+(\d+)\s*[:\.\-]?\s*(.*)$", "part_num"),
    (r"^\s*PART\s+(ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN)\s*[:\.\-]?\s*(.*)$", "part_word"),
    (r"^\s*Part\s+(One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten)\s*[:\.\-]?\s*(.*)$", "part_word"),
    (r"^\s*PART\s+([IVXLC]+)\s*[:\.\-]?\s*(.*)$", "part_roman"),

    # Special sections (prologue, epilogue, etc.)
    (r"^\s*(PROLOGUE|Prologue)\s*[:\.\-]?\s*(.*)$", "prologue"),
    (r"^\s*(EPILOGUE|Epilogue)\s*[:\.\-]?\s*(.*)$", "epilogue"),
    (r"^\s*(AFTERWORD|Afterword)\s*[:\.\-]?\s*(.*)$", "afterword"),
    (r"^\s*(FOREWORD|Foreword)\s*[:\.\-]?\s*(.*)$", "foreword"),
    (r"^\s*(PREFACE|Preface)\s*[:\.\-]?\s*(.*)$", "preface"),
    (r"^\s*(INTRODUCTION|Introduction)\s*[:\.\-]?\s*(.*)$", "introduction"),
    (r"^\s*(DEDICATION|Dedication)\s*[:\.\-]?\s*(.*)$", "dedication"),
    (r"^\s*(ACKNOWLEDGMENTS?|Acknowledgments?)\s*[:\.\-]?\s*(.*)$", "acknowledgments"),
    (r"^\s*(ABOUT\s+THE\s+AUTHOR|About\s+the\s+Author)\s*[:\.\-]?\s*(.*)$", "about_author"),
    (r"^\s*(GLOSSARY|Glossary)\s*[:\.\-]?\s*(.*)$", "glossary"),
    (r"^\s*(APPENDIX|Appendix)\s*[:\.\-]?\s*(.*)$", "appendix"),
]

# Word to number mapping
WORD_TO_NUM = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19, "twenty": 20,
}

# Roman numeral to number mapping
ROMAN_TO_NUM = {
    "i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5,
    "vi": 6, "vii": 7, "viii": 8, "ix": 9, "x": 10,
    "xi": 11, "xii": 12, "xiii": 13, "xiv": 14, "xv": 15,
    "xvi": 16, "xvii": 17, "xviii": 18, "xix": 19, "xx": 20,
    "xxi": 21, "xxii": 22, "xxiii": 23, "xxiv": 24, "xxv": 25,
    "xxx": 30, "xl": 40, "l": 50,
}

# Section type to segment type mapping (for Findaway)
SECTION_TO_SEGMENT = {
    "prologue": "front_matter",
    "foreword": "front_matter",
    "preface": "front_matter",
    "introduction": "front_matter",
    "dedication": "front_matter",
    "chapter_num": "body_chapter",
    "chapter_word": "body_chapter",
    "chapter_roman": "body_chapter",
    "part_num": "body_chapter",
    "part_word": "body_chapter",
    "part_roman": "body_chapter",
    "epilogue": "back_matter",
    "afterword": "back_matter",
    "acknowledgments": "back_matter",
    "about_author": "back_matter",
    "glossary": "back_matter",
    "appendix": "back_matter",
}


def _convert_to_number(value: str, pattern_type: str) -> int:
    """Convert various number formats to integer."""
    if pattern_type.endswith("_num"):
        return int(value)
    elif pattern_type.endswith("_word"):
        return WORD_TO_NUM.get(value.lower(), 0)
    elif pattern_type.endswith("_roman"):
        return ROMAN_TO_NUM.get(value.lower(), 0)
    else:
        # Special sections get high numbers to sort to front/back
        return 0


def _match_chapter_header(line: str) -> Optional[Tuple[str, str, str]]:
    """
    Try to match a line against chapter header patterns.

    Returns tuple of (pattern_type, number_part, title_part) or None
    """
    for pattern, pattern_type in CHAPTER_PATTERNS:
        match = re.match(pattern, line, re.IGNORECASE)
        if match:
            groups = match.groups()
            number_part = groups[0] if len(groups) > 0 else ""
            title_part = groups[1].strip() if len(groups) > 1 else ""
            return (pattern_type, number_part, title_part)
    return None


def split_into_chapters(
    book_text: str,
    detect_scene_breaks: bool = False,
    min_chapter_words: int = 100
) -> List[Dict]:
    """
    Split book text into chapters with deterministic ordering.

    Args:
        book_text: Full manuscript text
        detect_scene_breaks: If True, also split on *** or --- breaks (default False)
        min_chapter_words: Minimum words for a chapter to be valid

    Returns list of dicts:
        {
            "index": int,            # For backwards compatibility (1-based)
            "source_order": int,     # Original position in manuscript (0-based)
            "chapter_index": int,    # Same as source_order initially (0-based)
            "title": str,            # Chapter title
            "text": str,             # Chapter content
            "segment_type": str,     # Findaway segment type
            "pattern_type": str,     # What pattern matched (for debugging)
            "word_count": int,       # Word count
            "character_count": int,  # Character count
        }

    IMPORTANT: chapter_index starts at source_order but can be changed by user.
               source_order is NEVER changed - it's the original manuscript position.
    """
    lines = book_text.splitlines()
    chapters = []
    current_chapter = None
    current_lines = []
    source_order = 0

    def flush_chapter():
        """Save current chapter if it has content."""
        nonlocal current_chapter, current_lines, source_order

        if current_chapter is not None:
            text = "\n".join(current_lines).strip()
            word_count = len(text.split())

            # Only save if has minimum content
            if word_count >= min_chapter_words or len(chapters) == 0:
                current_chapter["text"] = text
                current_chapter["word_count"] = word_count
                current_chapter["character_count"] = len(text)
                current_chapter["source_order"] = source_order
                current_chapter["chapter_index"] = source_order  # Initially same
                current_chapter["index"] = source_order + 1  # 1-based for backwards compat
                chapters.append(current_chapter)
                source_order += 1
            else:
                logger.debug(f"Skipping short section ({word_count} words): {current_chapter.get('title', 'Untitled')}")

        current_lines = []
        current_chapter = None

    # Compile scene break pattern if needed
    scene_break_pattern = re.compile(r"^\s*(\*\s*\*\s*\*|\-\s*\-\s*\-|~\s*~\s*~)\s*$")

    for line in lines:
        # Check for chapter header
        header_match = _match_chapter_header(line)

        if header_match:
            pattern_type, number_part, title_part = header_match

            # Flush previous chapter
            flush_chapter()

            # Determine title
            if title_part:
                title = title_part
            elif pattern_type in ("prologue", "epilogue", "afterword", "foreword",
                                  "preface", "introduction", "dedication",
                                  "acknowledgments", "about_author", "glossary", "appendix"):
                title = number_part.title()  # "Prologue", "Epilogue", etc.
            else:
                # Use number in title
                num = _convert_to_number(number_part, pattern_type)
                if pattern_type.startswith("part"):
                    title = f"Part {num}"
                else:
                    title = f"Chapter {num}"
                if title_part:
                    title += f": {title_part}"

            # Start new chapter
            current_chapter = {
                "title": title,
                "segment_type": SECTION_TO_SEGMENT.get(pattern_type, "body_chapter"),
                "pattern_type": pattern_type,
            }

        elif detect_scene_breaks and scene_break_pattern.match(line):
            # Scene break - start new section
            flush_chapter()
            current_chapter = {
                "title": f"Section {source_order + 1}",
                "segment_type": "body_chapter",
                "pattern_type": "scene_break",
            }

        else:
            # Add line to current chapter (or pre-chapter content)
            if current_chapter is not None:
                current_lines.append(line)
            else:
                # Content before first chapter header
                # Start an implicit chapter
                current_chapter = {
                    "title": "Opening",
                    "segment_type": "front_matter",
                    "pattern_type": "implicit",
                }
                current_lines.append(line)

    # Flush final chapter
    flush_chapter()

    # If no chapters found at all, treat entire text as single chapter
    if not chapters and book_text.strip():
        text = book_text.strip()
        chapters.append({
            "index": 1,
            "source_order": 0,
            "chapter_index": 0,
            "title": "Chapter 1",
            "text": text,
            "segment_type": "body_chapter",
            "pattern_type": "single_chapter",
            "word_count": len(text.split()),
            "character_count": len(text),
        })
        logger.info("No chapter headers found - treating entire text as single chapter")

    logger.info(f"Parsed {len(chapters)} chapter(s) from manuscript")
    for ch in chapters:
        logger.debug(f"  {ch['source_order']}: {ch['title']} ({ch['word_count']} words) [{ch['segment_type']}]")

    return chapters


def extract_chapter(book_text: str, chapter_index: int) -> Optional[Dict]:
    """
    Extract a single chapter by index (0-based chapter_index or 1-based index).
    Returns dict with chapter data, or None if not found.
    """
    chapters = split_into_chapters(book_text)
    for chapter in chapters:
        if chapter["chapter_index"] == chapter_index or chapter["index"] == chapter_index:
            return chapter
    return None


def sanitize_title_for_filename(title: str, max_length: int = 50) -> str:
    """
    Clean chapter title for use in filenames.
    Safe for Windows, Mac, Linux, and R2/S3 storage.
    """
    # Remove or replace problematic characters
    safe_title = re.sub(r"[^\w\s\-]", "", title)
    # Collapse multiple spaces/underscores
    safe_title = re.sub(r"[\s_]+", "_", safe_title).strip("_")
    # Truncate if too long
    if len(safe_title) > max_length:
        safe_title = safe_title[:max_length].rstrip("_")
    # Ensure not empty
    return safe_title or "untitled"


def clean_text(text: str) -> str:
    """
    Clean unicode characters that can break TTS APIs.
    Replaces smart quotes, em-dashes, etc. with ASCII equivalents.
    """
    replacements = {
        "—": "-",        # Em dash
        "–": "-",        # En dash
        "…": "...",      # Ellipsis
        "'": "'",        # Smart single quote (opening)
        "'": "'",        # Smart single quote (closing)
        """: '"',        # Smart double quote (opening)
        """: '"',        # Smart double quote (closing)
        "«": '"',        # Guillemet left
        "»": '"',        # Guillemet right
        "‹": "'",        # Single guillemet left
        "›": "'",        # Single guillemet right
        "„": '"',        # Low double quote
        "‚": "'",        # Low single quote
        "\u00A0": " ",   # Non-breaking space
        "\u2003": " ",   # Em space
        "\u2002": " ",   # En space
        "\u2009": " ",   # Thin space
        "\u200B": "",    # Zero-width space
        "\u200C": "",    # Zero-width non-joiner
        "\u200D": "",    # Zero-width joiner
        "\uFEFF": "",    # BOM
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    return text.strip()


def detect_character_dialogue(text: str, character_name: str = "Vihan") -> List[Dict]:
    """
    Split text into narrator and character dialogue blocks.
    Returns list of dicts: {"speaker": "narrator" | "character", "text": str}

    For dual-voice audiobook generation.
    """
    parts = []
    lines = text.split("\n")

    current_block = ""
    current_speaker = "narrator"

    def flush():
        nonlocal current_block
        if current_block.strip():
            parts.append({
                "speaker": current_speaker,
                "text": current_block.strip()
            })
        current_block = ""

    for line in lines:
        line_clean = line.strip()

        # Detect character lines
        if line_clean.startswith(f"{character_name}:") or line_clean.startswith(f"{character_name} "):
            flush()
            current_speaker = "character"
            # Remove "CharacterName:" prefix
            current_block += line_clean.replace(f"{character_name}:", "").strip() + "\n"
        else:
            if current_speaker != "narrator":
                flush()
                current_speaker = "narrator"
            current_block += line_clean + "\n"

    flush()
    return parts


def reorder_chapters(chapters: List[Dict], new_order: List[int]) -> List[Dict]:
    """
    Reorder chapters based on new_order list.

    Args:
        chapters: List of chapter dicts
        new_order: List of source_order values in new order

    Returns:
        List of chapters with updated chapter_index values

    Example:
        chapters = [{"source_order": 0}, {"source_order": 1}, {"source_order": 2}]
        new_order = [2, 0, 1]  # Move chapter 2 to front
        result: [
            {"source_order": 2, "chapter_index": 0},
            {"source_order": 0, "chapter_index": 1},
            {"source_order": 1, "chapter_index": 2},
        ]
    """
    # Build lookup by source_order
    by_source = {ch["source_order"]: ch for ch in chapters}

    # Validate new_order
    if set(new_order) != set(by_source.keys()):
        raise ValueError("new_order must contain exactly the same source_order values")

    # Create reordered list
    reordered = []
    for new_idx, source_idx in enumerate(new_order):
        ch = by_source[source_idx].copy()
        ch["chapter_index"] = new_idx
        ch["index"] = new_idx + 1  # 1-based for backwards compat
        reordered.append(ch)

    return reordered


def get_segment_type_order(segment_type: str) -> int:
    """
    Get sort order for segment types (for Findaway-style ordering).

    Order: opening_credits < front_matter < body_chapter < back_matter < closing_credits < retail_sample
    """
    order_map = {
        "opening_credits": 0,
        "front_matter": 1,
        "body_chapter": 2,
        "back_matter": 3,
        "closing_credits": 4,
        "retail_sample": 5,
    }
    return order_map.get(segment_type, 2)


# ============================================================================
# FINDAWAY FILE NAMING
# ============================================================================
# File naming convention for Findaway distribution:
#   00_opening_credits.mp3      - Opening credits
#   01_front_matter_01.mp3      - Dedication, foreword, etc. (01-09 reserved)
#   10_chapter_01.mp3           - Body chapters start at 10
#   10_chapter_02.mp3, etc.
#   80_back_matter_01.mp3       - Epilogue, afterword, etc. (80-89 reserved)
#   98_closing_credits.mp3      - Closing credits
#   99_retail_sample.mp3        - Retail sample
# ============================================================================

FINDAWAY_PREFIXES = {
    "opening_credits": "00",
    "front_matter": "01",  # Can increment: 01, 02, ..., 09
    "body_chapter": "10",  # Starts at 10, increments: 10, 11, 12, ...
    "back_matter": "80",   # Can increment: 80, 81, ..., 89
    "closing_credits": "98",
    "retail_sample": "99",
}


def generate_findaway_filename(
    segment_type: str,
    index_within_type: int,
    title: str,
    extension: str = "mp3"
) -> str:
    """
    Generate a Findaway-compatible filename for an audio track.

    Args:
        segment_type: One of opening_credits, front_matter, body_chapter,
                      back_matter, closing_credits, retail_sample
        index_within_type: 0-based index within this segment type
                           (e.g., chapter 0, chapter 1, etc.)
        title: Chapter/section title for the filename
        extension: File extension (default "mp3")

    Returns:
        Findaway-style filename like "10_chapter_01.mp3"

    Examples:
        generate_findaway_filename("opening_credits", 0, "Opening Credits")
        -> "00_opening_credits.mp3"

        generate_findaway_filename("front_matter", 0, "Dedication")
        -> "01_dedication.mp3"

        generate_findaway_filename("body_chapter", 0, "Chapter 1: The Beginning")
        -> "10_chapter_01.mp3"

        generate_findaway_filename("body_chapter", 14, "Chapter 15")
        -> "24_chapter_15.mp3"

        generate_findaway_filename("closing_credits", 0, "Closing Credits")
        -> "98_closing_credits.mp3"
    """
    # Get base prefix for segment type
    base_prefix = FINDAWAY_PREFIXES.get(segment_type, "50")

    # Calculate actual prefix number based on index
    if segment_type == "opening_credits":
        prefix = "00"
    elif segment_type == "front_matter":
        # Front matter: 01-09
        prefix = f"{1 + index_within_type:02d}"
        if int(prefix) > 9:
            prefix = "09"  # Cap at 09
    elif segment_type == "body_chapter":
        # Body chapters: 10-79
        prefix = f"{10 + index_within_type:02d}"
        if int(prefix) > 79:
            prefix = "79"  # Cap at 79
    elif segment_type == "back_matter":
        # Back matter: 80-89
        prefix = f"{80 + index_within_type:02d}"
        if int(prefix) > 89:
            prefix = "89"  # Cap at 89
    elif segment_type == "closing_credits":
        prefix = "98"
    elif segment_type == "retail_sample":
        prefix = "99"
    else:
        prefix = f"{50 + index_within_type:02d}"

    # Generate safe filename from title
    safe_title = sanitize_title_for_filename(title.lower(), max_length=40)

    # For body chapters, use consistent naming
    if segment_type == "body_chapter":
        safe_title = f"chapter_{index_within_type + 1:02d}"

    return f"{prefix}_{safe_title}.{extension}"


def generate_track_list_from_chapters(
    chapters: List[Dict],
    include_credits: bool = True,
    include_retail_sample: bool = True,
    opening_credits_text: Optional[str] = None,
    closing_credits_text: Optional[str] = None,
    retail_sample_text: Optional[str] = None,
) -> List[Dict]:
    """
    Generate a complete track list with Findaway filenames from chapters.

    Args:
        chapters: List of chapter dicts from split_into_chapters()
        include_credits: Whether to include opening/closing credits tracks
        include_retail_sample: Whether to include retail sample track
        opening_credits_text: Text for opening credits (optional)
        closing_credits_text: Text for closing credits (optional)
        retail_sample_text: Text for retail sample (optional)

    Returns:
        List of track dicts with:
        {
            "track_index": int,       # 0-based playback order
            "segment_type": str,
            "title": str,
            "export_filename": str,   # Findaway filename
            "source_chapter_id": str or None,  # For linking back
            "text": str or None,
        }
    """
    tracks = []
    track_index = 0

    # Counters for each segment type
    front_matter_count = 0
    body_chapter_count = 0
    back_matter_count = 0

    # 1. Opening credits
    if include_credits:
        tracks.append({
            "track_index": track_index,
            "segment_type": "opening_credits",
            "title": "Opening Credits",
            "export_filename": generate_findaway_filename("opening_credits", 0, "Opening Credits"),
            "source_chapter_id": None,
            "text": opening_credits_text,
        })
        track_index += 1

    # Sort chapters by segment type order, then by chapter_index
    sorted_chapters = sorted(
        chapters,
        key=lambda c: (get_segment_type_order(c.get("segment_type", "body_chapter")), c.get("chapter_index", 0))
    )

    # 2. Process chapters by segment type
    for chapter in sorted_chapters:
        seg_type = chapter.get("segment_type", "body_chapter")
        title = chapter.get("title", "Untitled")

        if seg_type == "front_matter":
            export_filename = generate_findaway_filename("front_matter", front_matter_count, title)
            front_matter_count += 1
        elif seg_type == "body_chapter":
            export_filename = generate_findaway_filename("body_chapter", body_chapter_count, title)
            body_chapter_count += 1
        elif seg_type == "back_matter":
            export_filename = generate_findaway_filename("back_matter", back_matter_count, title)
            back_matter_count += 1
        else:
            # Default to body chapter
            export_filename = generate_findaway_filename("body_chapter", body_chapter_count, title)
            body_chapter_count += 1

        tracks.append({
            "track_index": track_index,
            "segment_type": seg_type,
            "title": title,
            "export_filename": export_filename,
            "source_chapter_id": chapter.get("id"),
            "text": chapter.get("text"),
            "word_count": chapter.get("word_count", 0),
        })
        track_index += 1

    # 3. Closing credits
    if include_credits:
        tracks.append({
            "track_index": track_index,
            "segment_type": "closing_credits",
            "title": "Closing Credits",
            "export_filename": generate_findaway_filename("closing_credits", 0, "Closing Credits"),
            "source_chapter_id": None,
            "text": closing_credits_text,
        })
        track_index += 1

    # 4. Retail sample (always at the end)
    if include_retail_sample:
        tracks.append({
            "track_index": track_index,
            "segment_type": "retail_sample",
            "title": "Retail Sample",
            "export_filename": generate_findaway_filename("retail_sample", 0, "Retail Sample"),
            "source_chapter_id": None,
            "text": retail_sample_text,
        })
        track_index += 1

    logger.info(f"Generated {len(tracks)} tracks with Findaway filenames")
    return tracks
