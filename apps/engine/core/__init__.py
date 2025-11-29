"""
Core Engine Modules
Shared utilities for text processing, chapter parsing, and Findaway exports
"""

from .chapter_parser import (
    split_into_chapters,
    extract_chapter,
    sanitize_title_for_filename,
    clean_text,
    detect_character_dialogue,
    reorder_chapters,
    get_segment_type_order,
    generate_findaway_filename,
    generate_track_list_from_chapters,
)
from .advanced_chunker import chunk_chapter_advanced, chunk_simple
from .retail_sample_selector import (
    select_retail_sample,
    format_sample_for_db,
)
from .findaway_planner import (
    build_findaway_section_plan,
    get_section_order,
    get_sections_for_tts,
    estimate_total_duration,
)

__all__ = [
    # Chapter parsing
    "split_into_chapters",
    "extract_chapter",
    "sanitize_title_for_filename",
    "clean_text",
    "detect_character_dialogue",
    "reorder_chapters",
    "get_segment_type_order",
    # Findaway file naming
    "generate_findaway_filename",
    "generate_track_list_from_chapters",
    # Chunking
    "chunk_chapter_advanced",
    "chunk_simple",
    # Retail sample selection
    "select_retail_sample",
    "format_sample_for_db",
    # Findaway planning
    "build_findaway_section_plan",
    "get_section_order",
    "get_sections_for_tts",
    "estimate_total_duration",
]
