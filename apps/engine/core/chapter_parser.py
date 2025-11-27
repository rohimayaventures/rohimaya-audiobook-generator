"""
Chapter Parser - Extract and parse chapters from book text
Integrated from husband's Peacock/Phoenix implementation
"""

import re
from typing import List, Dict, Optional


def split_into_chapters(book_text: str) -> List[Dict]:
    """
    Split book text into chapters based on "CHAPTER N" headers.
    If no chapter headers found, treats entire text as a single chapter.

    Returns list of dicts:
        {
            "index": int,        # Chapter number (1-based)
            "title": str,        # Chapter title (or "Chapter N" if no title)
            "text": str          # Chapter content (without header)
        }

    Algorithm from husband's generate_full_book.py
    """
    lines = book_text.splitlines()
    chapters = []
    current_title = None
    current_lines = []
    current_index = None

    # Match: "CHAPTER 1", "CHAPTER 1:", "CHAPTER 1 - Title", etc.
    chapter_header_regex = re.compile(
        r"^\s*CHAPTER\s+(\d+)\s*[:\-]?\s*(.*)$",
        re.IGNORECASE
    )

    for line in lines:
        match = chapter_header_regex.match(line)
        if match:
            # Flush previous chapter
            if current_title is not None:
                chapters.append({
                    "index": current_index,
                    "title": current_title.strip() or f"Chapter {current_index}",
                    "text": "\n".join(current_lines).strip()
                })
                current_lines = []

            # Start new chapter
            current_index = int(match.group(1))
            possible_title = match.group(2).strip()
            current_title = possible_title if possible_title else f"Chapter {current_index}"
        else:
            if current_title is not None:
                current_lines.append(line)

    # Flush last chapter
    if current_title is not None and current_lines:
        chapters.append({
            "index": current_index,
            "title": current_title.strip() or f"Chapter {current_index}",
            "text": "\n".join(current_lines).strip()
        })

    # Sort by index just in case
    chapters.sort(key=lambda c: c["index"])

    # If no chapters found, treat entire text as a single chapter
    if not chapters and book_text.strip():
        chapters.append({
            "index": 1,
            "title": "Chapter 1",
            "text": book_text.strip()
        })

    return chapters


def extract_chapter(book_text: str, chapter_number: int) -> Optional[Dict]:
    """
    Extract a single chapter by number.
    Returns dict with index, title, text, or None if not found.
    """
    chapters = split_into_chapters(book_text)
    for chapter in chapters:
        if chapter["index"] == chapter_number:
            return chapter
    return None


def sanitize_title_for_filename(title: str) -> str:
    """
    Clean chapter title for use in filenames.
    From husband's implementation.
    """
    # Remove special characters, keep alphanumeric, spaces, hyphens
    safe_title = re.sub(r"[^\w\s\-]", "", title)
    # Collapse multiple spaces
    safe_title = re.sub(r"\s+", " ", safe_title).strip()
    return safe_title


def clean_text(text: str) -> str:
    """
    Clean unicode characters that can break TTS APIs.
    From husband's generate_chapters.py
    """
    replacements = {
        "—": "-",        # Em dash
        "–": "-",        # En dash
        "…": "...",      # Ellipsis
        "'": "'",        # Smart single quote
        "'": "'",        # Smart single quote (closing)
        """: '"',        # Smart double quote (opening)
        """: '"',        # Smart double quote (closing)
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    return text.strip()


# Character detection for dual-voice mode
def detect_character_dialogue(text: str, character_name: str = "Vihan") -> List[Dict]:
    """
    Split text into narrator and character dialogue blocks.
    Returns list of dicts: {"speaker": "narrator" | "character", "text": str}

    From husband's generate_dualvoice_ch1.py
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

        # Detect character lines (simple pattern: "CharacterName:" or starts with name)
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
