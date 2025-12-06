"""
Unit tests for chapter_parser module.

Tests cover:
- Chapter detection patterns (numbered, word, roman numerals)
- POV marker and scene break filtering
- Front matter detection (prologue, dedication, etc.)
- Back matter detection (epilogue, acknowledgments, etc.)
- Teaser/bonus chapter detection
- Segment type assignment
- Segment order calculation
- Filename generation for Findaway
"""

import pytest
import sys
from pathlib import Path

# Add the core directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.chapter_parser import (
    split_into_chapters,
    _should_skip_line,
    _match_chapter_header,
    get_segment_type_order,
    calculate_segment_order,
    assign_segment_orders,
    generate_findaway_filename,
    sanitize_title_for_filename,
    clean_text,
    SECTION_TO_SEGMENT,
)


class TestChapterDetection:
    """Test chapter header detection patterns."""

    def test_chapter_with_number(self):
        """Test detection of 'CHAPTER 1' style headers."""
        # Note: Parser creates implicit "Opening" chapter for content before first header
        # We use strip() text to start with the header
        text = """CHAPTER 1

This is the first chapter content.

CHAPTER 2

This is the second chapter content.
"""
        chapters = split_into_chapters(text, min_chapter_words=5)
        # Find body chapters
        body_chapters = [c for c in chapters if c["segment_type"] == "body_chapter"]
        assert len(body_chapters) == 2
        assert body_chapters[0]["title"] == "Chapter 1"
        assert body_chapters[1]["title"] == "Chapter 2"

    def test_chapter_with_word_number(self):
        """Test detection of 'Chapter One' style headers."""
        text = """Chapter One

This is the first chapter content here.

Chapter Two

This is the second chapter content here.
"""
        chapters = split_into_chapters(text, min_chapter_words=5)
        body_chapters = [c for c in chapters if c["segment_type"] == "body_chapter"]
        assert len(body_chapters) == 2
        assert body_chapters[0]["title"] == "Chapter 1"
        assert body_chapters[1]["title"] == "Chapter 2"

    def test_chapter_with_roman_numerals(self):
        """Test detection of 'Chapter I, II, III' style headers."""
        text = """CHAPTER I

This is the first chapter content here.

CHAPTER II

This is the second chapter content here.

CHAPTER III

This is the third chapter content here.
"""
        chapters = split_into_chapters(text, min_chapter_words=5)
        body_chapters = [c for c in chapters if c["segment_type"] == "body_chapter"]
        assert len(body_chapters) == 3
        assert body_chapters[0]["title"] == "Chapter 1"
        assert body_chapters[1]["title"] == "Chapter 2"
        assert body_chapters[2]["title"] == "Chapter 3"

    def test_chapter_with_title(self):
        """Test detection of 'CHAPTER 1: The Beginning' style headers."""
        text = """CHAPTER 1: The Beginning

This is the first chapter content here.

CHAPTER 2: The Journey

This is the second chapter content here.
"""
        chapters = split_into_chapters(text, min_chapter_words=5)
        body_chapters = [c for c in chapters if c["segment_type"] == "body_chapter"]
        assert len(body_chapters) == 2
        assert body_chapters[0]["title"] == "The Beginning"
        assert body_chapters[1]["title"] == "The Journey"


class TestPOVFiltering:
    """Test POV marker and scene break filtering."""

    def test_pov_markers_asterisk(self):
        """Test that *** ARIA *** style POV markers are skipped."""
        assert _should_skip_line("*** ARIA ***") is True
        assert _should_skip_line("*** Aria's POV ***") is True
        assert _should_skip_line("  *** VIHAN ***  ") is True

    def test_pov_markers_tilde(self):
        """Test that ~~~ NAME ~~~ style POV markers are skipped."""
        assert _should_skip_line("~~~ ARIA ~~~") is True
        assert _should_skip_line("~~~VIHAN~~~") is True

    def test_pov_markers_dash(self):
        """Test that --- NAME --- style POV markers are skipped."""
        assert _should_skip_line("--- ARIA ---") is True
        assert _should_skip_line("---VIHAN---") is True

    def test_scene_breaks(self):
        """Test that scene break dividers are skipped."""
        assert _should_skip_line("***") is True
        assert _should_skip_line("---") is True
        assert _should_skip_line("~~~") is True
        assert _should_skip_line("===") is True
        assert _should_skip_line("* * *") is True
        assert _should_skip_line("- - -") is True

    def test_pov_labels(self):
        """Test that POV labels are skipped."""
        assert _should_skip_line("POV: Aria") is True
        assert _should_skip_line("[POV: Vihan]") is True
        assert _should_skip_line("(Aria's POV)") is True
        assert _should_skip_line("Aria's POV") is True
        assert _should_skip_line("VIHAN POV") is True

    def test_all_caps_names(self):
        """Test that ALL CAPS names (likely POV indicators) are skipped."""
        assert _should_skip_line("ARIA") is True
        assert _should_skip_line("VIHAN") is True
        # Single letter should not be skipped
        assert _should_skip_line("A") is False

    def test_valid_content_not_skipped(self):
        """Test that valid chapter content is not skipped."""
        assert _should_skip_line("This is normal text.") is False
        assert _should_skip_line("Chapter 1") is False
        assert _should_skip_line("CHAPTER ONE") is False
        assert _should_skip_line("The Beginning") is False
        assert _should_skip_line("Aria walked into the room.") is False

    def test_pov_markers_dont_create_chapters(self):
        """Test that POV markers don't create spurious chapters."""
        text = """
CHAPTER 1

This is the first chapter content here.

*** ARIA ***

Aria's perspective on things.

*** VIHAN ***

Vihan's perspective on things.

CHAPTER 2

This is the second chapter content here.
"""
        chapters = split_into_chapters(text, min_chapter_words=5)
        # Should only have 2 chapters, not 4
        assert len(chapters) == 2
        assert chapters[0]["title"] == "Chapter 1"
        assert chapters[1]["title"] == "Chapter 2"
        # POV markers should be included as content
        assert "ARIA" in chapters[0]["text"] or "Aria" in chapters[0]["text"]


class TestFrontMatterDetection:
    """Test front matter section detection."""

    def test_prologue(self):
        """Test prologue detection."""
        text = """
PROLOGUE

This is the prologue content here now.

CHAPTER 1

This is the first chapter content.
"""
        chapters = split_into_chapters(text, min_chapter_words=5)
        assert len(chapters) == 2
        assert chapters[0]["segment_type"] == "front_matter"
        assert "Prologue" in chapters[0]["title"]

    def test_dedication(self):
        """Test dedication detection."""
        text = """
DEDICATION

To my family and friends.

CHAPTER 1

This is the first chapter content.
"""
        chapters = split_into_chapters(text, min_chapter_words=5)
        assert len(chapters) == 2
        assert chapters[0]["segment_type"] == "front_matter"

    def test_foreword(self):
        """Test foreword detection."""
        text = """
FOREWORD

This is a foreword written by someone.

CHAPTER 1

This is the first chapter content.
"""
        chapters = split_into_chapters(text, min_chapter_words=5)
        assert len(chapters) == 2
        assert chapters[0]["segment_type"] == "front_matter"

    def test_authors_note(self):
        """Test author's note detection."""
        text = """
AUTHOR'S NOTE

A note from the author about things.

CHAPTER 1

This is the first chapter content.
"""
        chapters = split_into_chapters(text, min_chapter_words=5)
        assert len(chapters) == 2
        assert chapters[0]["segment_type"] == "front_matter"

    def test_content_warning(self):
        """Test content warning detection."""
        text = """
CONTENT WARNING

This book contains mature themes.

CHAPTER 1

This is the first chapter content.
"""
        chapters = split_into_chapters(text, min_chapter_words=5)
        assert len(chapters) == 2
        assert chapters[0]["segment_type"] == "front_matter"


class TestBackMatterDetection:
    """Test back matter section detection."""

    def test_epilogue(self):
        """Test epilogue detection."""
        text = """
CHAPTER 1

This is the first chapter content.

EPILOGUE

This is the epilogue content here now.
"""
        chapters = split_into_chapters(text, min_chapter_words=5)
        assert len(chapters) == 2
        assert chapters[1]["segment_type"] == "back_matter"
        assert "Epilogue" in chapters[1]["title"]

    def test_acknowledgments(self):
        """Test acknowledgments detection."""
        text = """
CHAPTER 1

This is the first chapter content.

ACKNOWLEDGMENTS

Thanks to everyone who helped with this.
"""
        chapters = split_into_chapters(text, min_chapter_words=5)
        assert len(chapters) == 2
        assert chapters[1]["segment_type"] == "back_matter"

    def test_about_author(self):
        """Test 'About the Author' detection."""
        text = """
CHAPTER 1

This is the first chapter content.

ABOUT THE AUTHOR

The author lives somewhere nice.
"""
        chapters = split_into_chapters(text, min_chapter_words=5)
        assert len(chapters) == 2
        assert chapters[1]["segment_type"] == "back_matter"


class TestTeaserBonusDetection:
    """Test teaser and bonus chapter detection."""

    def test_sneak_peek(self):
        """Test 'Sneak Peek' teaser detection."""
        text = """
CHAPTER 1

This is the first chapter content.

SNEAK PEEK

Preview of the next book coming soon.
"""
        chapters = split_into_chapters(text, min_chapter_words=5)
        assert len(chapters) == 2
        assert chapters[1]["segment_type"] == "teaser_chapter"

    def test_bonus_chapter(self):
        """Test 'Bonus Chapter' detection."""
        text = """
CHAPTER 1

This is the first chapter content.

BONUS CHAPTER

Extra content for readers who made it.
"""
        chapters = split_into_chapters(text, min_chapter_words=5)
        assert len(chapters) == 2
        assert chapters[1]["segment_type"] == "bonus_chapter"

    def test_excerpt_from(self):
        """Test 'Excerpt from' teaser detection."""
        text = """
CHAPTER 1

This is the first chapter content.

EXCERPT FROM: The Next Adventure

A preview of the upcoming book here.
"""
        chapters = split_into_chapters(text, min_chapter_words=5)
        assert len(chapters) == 2
        assert chapters[1]["segment_type"] == "teaser_chapter"

    def test_deleted_scene(self):
        """Test 'Deleted Scene' bonus detection."""
        text = """
CHAPTER 1

This is the first chapter content.

DELETED SCENE

A scene that was cut from the book.
"""
        chapters = split_into_chapters(text, min_chapter_words=5)
        assert len(chapters) == 2
        assert chapters[1]["segment_type"] == "bonus_chapter"

    def test_extended_epilogue(self):
        """Test 'Extended Epilogue' bonus detection."""
        text = """
CHAPTER 1

This is the first chapter content.

EXTENDED EPILOGUE

More content after the main epilogue.
"""
        chapters = split_into_chapters(text, min_chapter_words=5)
        assert len(chapters) == 2
        assert chapters[1]["segment_type"] == "bonus_chapter"


class TestSegmentTypeOrder:
    """Test segment type ordering for Findaway."""

    def test_segment_type_order(self):
        """Test correct ordering of segment types."""
        assert get_segment_type_order("opening_credits") == 0
        assert get_segment_type_order("front_matter") == 1
        assert get_segment_type_order("body_chapter") == 2
        assert get_segment_type_order("back_matter") == 3
        assert get_segment_type_order("bonus_chapter") == 4
        assert get_segment_type_order("teaser_chapter") == 5
        assert get_segment_type_order("closing_credits") == 6
        assert get_segment_type_order("retail_sample") == 7

    def test_unknown_type_defaults_to_body(self):
        """Test that unknown types default to body_chapter order."""
        assert get_segment_type_order("unknown") == 2


class TestSegmentOrderCalculation:
    """Test segment order calculation for Findaway ranges."""

    def test_opening_credits_order(self):
        """Test opening credits always gets order 0."""
        assert calculate_segment_order("opening_credits", 0) == 0
        assert calculate_segment_order("opening_credits", 1) == 0

    def test_front_matter_order_range(self):
        """Test front matter gets orders 1-9."""
        assert calculate_segment_order("front_matter", 0) == 1
        assert calculate_segment_order("front_matter", 1) == 2
        assert calculate_segment_order("front_matter", 8) == 9
        # Should cap at 9
        assert calculate_segment_order("front_matter", 10) == 9

    def test_body_chapter_order_range(self):
        """Test body chapters get orders 10-79."""
        assert calculate_segment_order("body_chapter", 0) == 10
        assert calculate_segment_order("body_chapter", 1) == 11
        assert calculate_segment_order("body_chapter", 69) == 79
        # Should cap at 79
        assert calculate_segment_order("body_chapter", 100) == 79

    def test_back_matter_order_range(self):
        """Test back matter gets orders 80-89."""
        assert calculate_segment_order("back_matter", 0) == 80
        assert calculate_segment_order("back_matter", 9) == 89
        # Should cap at 89
        assert calculate_segment_order("back_matter", 15) == 89

    def test_bonus_chapter_order_range(self):
        """Test bonus chapters get orders 90-94."""
        assert calculate_segment_order("bonus_chapter", 0) == 90
        assert calculate_segment_order("bonus_chapter", 4) == 94
        # Should cap at 94
        assert calculate_segment_order("bonus_chapter", 10) == 94

    def test_teaser_chapter_order_range(self):
        """Test teaser chapters get orders 95-97."""
        assert calculate_segment_order("teaser_chapter", 0) == 95
        assert calculate_segment_order("teaser_chapter", 2) == 97
        # Should cap at 97
        assert calculate_segment_order("teaser_chapter", 5) == 97

    def test_closing_credits_order(self):
        """Test closing credits always gets order 98."""
        assert calculate_segment_order("closing_credits", 0) == 98

    def test_retail_sample_order(self):
        """Test retail sample always gets order 99."""
        assert calculate_segment_order("retail_sample", 0) == 99


class TestFindawayFilenameGeneration:
    """Test Findaway-style filename generation."""

    def test_opening_credits_filename(self):
        """Test opening credits filename."""
        filename = generate_findaway_filename("opening_credits", 0, "Opening Credits")
        assert filename == "00_opening_credits.mp3"

    def test_front_matter_filename(self):
        """Test front matter filename."""
        filename = generate_findaway_filename("front_matter", 0, "Dedication")
        assert filename == "01_dedication.mp3"

        filename = generate_findaway_filename("front_matter", 1, "Prologue")
        assert filename == "02_prologue.mp3"

    def test_body_chapter_filename(self):
        """Test body chapter filename with sequential numbering."""
        filename = generate_findaway_filename("body_chapter", 0, "Chapter 1: The Beginning")
        assert filename == "10_chapter_01.mp3"

        filename = generate_findaway_filename("body_chapter", 14, "Chapter 15")
        assert filename == "24_chapter_15.mp3"

    def test_back_matter_filename(self):
        """Test back matter filename."""
        filename = generate_findaway_filename("back_matter", 0, "Epilogue")
        assert filename == "80_epilogue.mp3"

    def test_bonus_chapter_filename(self):
        """Test bonus chapter filename."""
        filename = generate_findaway_filename("bonus_chapter", 0, "Deleted Scene")
        assert filename == "90_bonus_01.mp3"

        filename = generate_findaway_filename("bonus_chapter", 1, "Extended Epilogue")
        assert filename == "91_bonus_02.mp3"

    def test_teaser_chapter_filename(self):
        """Test teaser chapter filename."""
        filename = generate_findaway_filename("teaser_chapter", 0, "Sneak Peek")
        assert filename == "95_teaser_01.mp3"

        filename = generate_findaway_filename("teaser_chapter", 1, "Preview")
        assert filename == "96_teaser_02.mp3"

    def test_closing_credits_filename(self):
        """Test closing credits filename."""
        filename = generate_findaway_filename("closing_credits", 0, "Closing Credits")
        assert filename == "98_closing_credits.mp3"

    def test_retail_sample_filename(self):
        """Test retail sample filename."""
        filename = generate_findaway_filename("retail_sample", 0, "Retail Sample")
        assert filename == "99_retail_sample.mp3"


class TestHelperFunctions:
    """Test helper functions."""

    def test_sanitize_title_basic(self):
        """Test basic title sanitization."""
        assert sanitize_title_for_filename("Chapter 1") == "Chapter_1"
        assert sanitize_title_for_filename("The Beginning!") == "The_Beginning"

    def test_sanitize_title_special_chars(self):
        """Test removal of special characters."""
        assert sanitize_title_for_filename("Chapter: 1 - The Beginning") == "Chapter_1_The_Beginning"
        assert sanitize_title_for_filename("Test!@#$%^&*()") == "Test"

    def test_sanitize_title_length(self):
        """Test title length truncation."""
        long_title = "A" * 100
        result = sanitize_title_for_filename(long_title, max_length=50)
        assert len(result) <= 50

    def test_clean_text_smart_quotes(self):
        """Test smart quote replacement."""
        # Use unicode escapes to avoid encoding issues
        smart_text = '\u201cHello,\u201d she said. \u201cIt\u2019s nice.\u201d'
        text = clean_text(smart_text)
        assert '"' in text
        assert "'" in text
        # Smart quotes should be replaced
        assert '\u201c' not in text  # left double quote
        assert '\u201d' not in text  # right double quote
        assert '\u2019' not in text  # right single quote

    def test_clean_text_em_dash(self):
        """Test em-dash replacement."""
        # Use unicode escape for em-dash
        text = clean_text("He said\u2014nothing.")
        assert '\u2014' not in text  # em-dash
        assert "-" in text


class TestAssignSegmentOrders:
    """Test the assign_segment_orders function."""

    def test_assign_orders_mixed_types(self):
        """Test segment order assignment for mixed chapter types."""
        chapters = [
            {"title": "Prologue", "segment_type": "front_matter"},
            {"title": "Chapter 1", "segment_type": "body_chapter"},
            {"title": "Chapter 2", "segment_type": "body_chapter"},
            {"title": "Epilogue", "segment_type": "back_matter"},
            {"title": "Bonus Scene", "segment_type": "bonus_chapter"},
            {"title": "Sneak Peek", "segment_type": "teaser_chapter"},
        ]

        result = assign_segment_orders(chapters)

        # Check correct number of chapters
        assert len(result) == 6

        # Check segment orders are in correct ranges
        orders = [ch["segment_order"] for ch in result]
        assert orders[0] == 1   # front_matter
        assert orders[1] == 10  # body_chapter (first)
        assert orders[2] == 11  # body_chapter (second)
        assert orders[3] == 80  # back_matter
        assert orders[4] == 90  # bonus_chapter
        assert orders[5] == 95  # teaser_chapter

    def test_assign_orders_sorted_by_segment_order(self):
        """Test that result is sorted by segment_order."""
        chapters = [
            {"title": "Chapter 1", "segment_type": "body_chapter"},
            {"title": "Prologue", "segment_type": "front_matter"},
            {"title": "Epilogue", "segment_type": "back_matter"},
        ]

        result = assign_segment_orders(chapters)

        # Should be sorted: front_matter, body_chapter, back_matter
        assert result[0]["segment_type"] == "front_matter"
        assert result[1]["segment_type"] == "body_chapter"
        assert result[2]["segment_type"] == "back_matter"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
