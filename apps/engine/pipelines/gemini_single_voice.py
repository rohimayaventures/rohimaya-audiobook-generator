"""
Gemini Single-Voice Pipeline
Full-book audiobook generation with Gemini TTS and multilingual support

Features:
- Voice presets with emotion/style control
- Input language detection
- Output language translation
- 40+ supported languages
"""

import os
import logging
import asyncio
from pathlib import Path
from typing import List, Dict, Optional, Callable, Any

from core.chapter_parser import split_into_chapters, sanitize_title_for_filename, clean_text
from core.advanced_chunker import chunk_chapter_advanced

logger = logging.getLogger(__name__)

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False


class GeminiSingleVoicePipeline:
    """
    Full-book audiobook generation pipeline using Gemini TTS.

    Supports:
    - Voice presets with emotion/style control
    - Input/output language selection
    - Translation for multilingual audiobooks
    """

    def __init__(
        self,
        voice_preset_id: str = "studio_neutral",
        input_language_code: str = "en-US",
        output_language_code: Optional[str] = None,
        emotion_style_prompt: Optional[str] = None,
        max_words_per_chunk: int = 500,
        max_chars_per_chunk: Optional[int] = None,
    ):
        """
        Initialize the Gemini single voice pipeline.

        Args:
            voice_preset_id: Voice preset ID (e.g., "narrator_female_warm")
            input_language_code: Language of the manuscript (or "auto" to detect)
            output_language_code: Desired output language (None to keep same as input)
            emotion_style_prompt: Custom style/emotion instructions
            max_words_per_chunk: Maximum words per chunk
            max_chars_per_chunk: Maximum characters per chunk (defaults to env var)
        """
        self.voice_preset_id = voice_preset_id
        self.input_language_code = input_language_code
        self.output_language_code = output_language_code or input_language_code
        self.emotion_style_prompt = emotion_style_prompt
        self.max_words = max_words_per_chunk

        # Get max chars from environment or use provided value
        env_max_chars = int(os.getenv("GOOGLE_TTS_MAX_CHARS_PER_SEGMENT", "2800"))
        self.max_chars = max_chars_per_chunk or env_max_chars

        # Initialize TTS
        from tts import GeminiTTS
        self.tts = GeminiTTS()

        logger.info(f"Gemini Pipeline initialized:")
        logger.info(f"  Voice preset: {voice_preset_id}")
        logger.info(f"  Input language: {input_language_code}")
        logger.info(f"  Output language: {self.output_language_code}")
        logger.info(f"  Max chars per chunk: {self.max_chars}")

    async def generate_audio_chunk(
        self,
        text: str,
        output_path: Path,
        chunk_info: str = "",
    ) -> bool:
        """
        Generate audio from text chunk using Gemini TTS.

        Args:
            text: Text to synthesize
            output_path: Path to save audio file
            chunk_info: Description for logging

        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"   🎙️ Generating audio: {output_path.name}")

            # Import here to avoid circular imports
            from tts import synthesize_segment

            # Generate audio with translation if needed
            audio_bytes = await synthesize_segment(
                text=text,
                preset_id=self.voice_preset_id,
                input_language_code=self.input_language_code,
                output_language_code=self.output_language_code,
                emotion_style_prompt=self.emotion_style_prompt,
            )

            # Write to file
            with open(output_path, "wb") as f:
                f.write(audio_bytes)

            print(f"   ✅ Saved: {output_path.name}")
            return True

        except Exception as e:
            print(f"   ❌ Failed to generate {output_path.name}: {e}")
            logger.error(f"TTS generation failed: {e}")
            return False

    def merge_chunks_pydub(self, chunk_paths: List[Path], final_path: Path) -> bool:
        """
        Merge audio chunks using pydub.

        Args:
            chunk_paths: List of paths to audio chunks
            final_path: Path for merged output

        Returns:
            True if successful
        """
        if not PYDUB_AVAILABLE:
            print("   ❌ pydub not available for merging")
            return False

        if not chunk_paths:
            print("   ❌ No chunks to merge")
            return False

        if len(chunk_paths) == 1:
            import shutil
            shutil.copy2(chunk_paths[0], final_path)
            print(f"   ✅ Copied single chunk to: {final_path.name}")
            return True

        try:
            print(f"   🔄 Merging {len(chunk_paths)} chunks...")
            final_audio = AudioSegment.empty()

            for chunk_path in chunk_paths:
                if not chunk_path.exists():
                    print(f"   ⚠️ Chunk not found: {chunk_path}")
                    continue

                segment = AudioSegment.from_mp3(str(chunk_path))
                final_audio += segment

            final_audio.export(str(final_path), format="mp3", bitrate="320k")
            print(f"   ✅ Merged: {final_path.name}")
            return True

        except Exception as e:
            print(f"   ❌ Merge failed: {e}")
            return False

    async def generate_chapter(
        self,
        chapter: Dict,
        output_dir: Path,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> Optional[Path]:
        """
        Generate audio for a single chapter.

        Args:
            chapter: Dict with "index", "title", "text"
            output_dir: Directory to save output files
            progress_callback: Optional callback for progress updates

        Returns:
            Path to final chapter audio file, or None if failed
        """
        idx = chapter["index"]
        title = chapter["title"]
        text = clean_text(chapter["text"])

        if not text.strip():
            print(f"   ⚠️ Skipping empty Chapter {idx:02d}")
            return None

        print(f"\n🎧 Chapter {idx:02d}: {title}")
        print(f"   Length: {len(text)} chars, ~{len(text.split())} words")

        # Chunk the chapter
        chunks = chunk_chapter_advanced(text, self.max_words, self.max_chars)
        print(f"   Split into {len(chunks)} chunk(s)")

        # Generate audio for each chunk
        chunk_paths = []
        safe_title = sanitize_title_for_filename(title)

        for i, chunk in enumerate(chunks, start=1):
            chunk_filename = f"Chapter {idx:02d} - {safe_title} - part{i}.mp3"
            chunk_path = output_dir / chunk_filename

            if await self.generate_audio_chunk(chunk, chunk_path, f"Chapter {idx}, Part {i}"):
                chunk_paths.append(chunk_path)
            else:
                print(f"   ⚠️ Failed chunk {i}/{len(chunks)}")

            if progress_callback:
                progress = (i / len(chunks)) * 100
                progress_callback(progress, f"Chapter {idx}: {i}/{len(chunks)} chunks")

        if not chunk_paths:
            print(f"   ❌ No audio generated for Chapter {idx:02d}")
            return None

        # Merge chunks into final chapter file
        final_filename = f"Chapter {idx:02d} - {safe_title} (final).mp3"
        final_path = output_dir / final_filename

        if self.merge_chunks_pydub(chunk_paths, final_path):
            print(f"   ✅ Chapter {idx:02d} complete!")
            return final_path
        else:
            print(f"   ⚠️ Merge failed, but individual chunks saved")
            return None

    async def generate_full_book(
        self,
        book_text: str,
        output_dir: Path,
        book_title: str = "Audiobook",
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> List[Path]:
        """
        Generate audiobook for entire book.

        Args:
            book_text: Full book text
            output_dir: Directory to save output files
            book_title: Title for the final merged audiobook file
            progress_callback: Optional callback for progress updates

        Returns:
            List of paths to audio files (chapters + final merged file as last item)
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        print("=" * 60)
        print("📘 Starting Full Book Generation (Gemini TTS)")
        print(f"   Voice: {self.voice_preset_id}")
        print(f"   Input Language: {self.input_language_code}")
        print(f"   Output Language: {self.output_language_code}")
        if self.emotion_style_prompt:
            print(f"   Style: {self.emotion_style_prompt}")
        print("=" * 60)

        # Split into chapters
        chapters = split_into_chapters(book_text)
        print(f"\nℹ️ Found {len(chapters)} chapter(s)")

        if not chapters:
            print("❌ No chapters found!")
            return []

        # Generate each chapter
        chapter_paths = []
        total_chapters = len(chapters)

        for i, chapter in enumerate(chapters):
            if progress_callback:
                base_progress = (i / total_chapters) * 80  # 0-80% for chapters
                progress_callback(base_progress, f"Processing chapter {i+1}/{total_chapters}")

            final_path = await self.generate_chapter(chapter, output_dir, progress_callback)
            if final_path:
                chapter_paths.append(final_path)

        if not chapter_paths:
            print("❌ No chapters generated!")
            return []

        # Merge all chapters into final audiobook
        safe_title = sanitize_title_for_filename(book_title)
        final_book_path = output_dir / f"{safe_title}_COMPLETE.mp3"

        print(f"\n📚 Merging {len(chapter_paths)} chapters into final audiobook...")
        if progress_callback:
            progress_callback(90, "Merging chapters into final audiobook")

        if self.merge_chunks_pydub(chapter_paths, final_book_path):
            print(f"✅ Final audiobook: {final_book_path.name}")
        else:
            print("⚠️ Could not merge chapters, using last chapter as output")
            final_book_path = chapter_paths[-1]

        if progress_callback:
            progress_callback(100, "Complete!")

        print("\n" + "=" * 60)
        print(f"✅ Book Generation Complete!")
        print(f"   Generated {len(chapter_paths)}/{len(chapters)} chapters")
        print(f"   Output: {output_dir}")
        print("=" * 60)

        # Return all chapter paths plus the final merged file
        return chapter_paths + [final_book_path]


async def generate_gemini_audiobook(
    manuscript_text: str,
    output_dir: Path,
    voice_preset_id: str = "studio_neutral",
    input_language_code: str = "en-US",
    output_language_code: Optional[str] = None,
    emotion_style_prompt: Optional[str] = None,
    book_title: str = "Audiobook",
    progress_callback: Optional[Callable[[float, str], None]] = None,
) -> List[Path]:
    """
    Convenience function to generate a Gemini-powered audiobook.

    Args:
        manuscript_text: Full book text
        output_dir: Directory to save output files
        voice_preset_id: Voice preset ID
        input_language_code: Input language (or "auto" to detect)
        output_language_code: Output language (None to keep same as input)
        emotion_style_prompt: Custom style/emotion instructions
        book_title: Title for the final merged audiobook file
        progress_callback: Optional callback for progress updates

    Returns:
        List of paths to generated audio files (final merged file is last)
    """
    pipeline = GeminiSingleVoicePipeline(
        voice_preset_id=voice_preset_id,
        input_language_code=input_language_code,
        output_language_code=output_language_code,
        emotion_style_prompt=emotion_style_prompt,
    )

    return await pipeline.generate_full_book(
        manuscript_text,
        output_dir,
        book_title,
        progress_callback,
    )


# Synchronous wrapper for backwards compatibility
def generate_gemini_audiobook_sync(
    manuscript_text: str,
    output_dir: Path,
    voice_preset_id: str = "studio_neutral",
    input_language_code: str = "en-US",
    output_language_code: Optional[str] = None,
    emotion_style_prompt: Optional[str] = None,
    book_title: str = "Audiobook",
) -> List[Path]:
    """
    Synchronous wrapper for generate_gemini_audiobook.

    Use this when calling from synchronous code.
    """
    return asyncio.run(
        generate_gemini_audiobook(
            manuscript_text=manuscript_text,
            output_dir=output_dir,
            voice_preset_id=voice_preset_id,
            input_language_code=input_language_code,
            output_language_code=output_language_code,
            emotion_style_prompt=emotion_style_prompt,
            book_title=book_title,
        )
    )
