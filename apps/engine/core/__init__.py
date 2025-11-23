"""
Core Engine Modules
Shared utilities for text processing and chapter parsing
"""

from .chapter_parser import (
    split_into_chapters,
    extract_chapter,
    sanitize_title_for_filename,
    clean_text,
    detect_character_dialogue
)
from .advanced_chunker import chunk_chapter_advanced, chunk_simple

__all__ = [
    "split_into_chapters",
    "extract_chapter",
    "sanitize_title_for_filename",
    "clean_text",
    "detect_character_dialogue",
    "chunk_chapter_advanced",
    "chunk_simple"
]
