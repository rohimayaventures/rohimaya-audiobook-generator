"""
Standard Single-Voice Pipeline
Full-book audiobook generation with a single narrator voice
Integrated from husband's generate_full_book.py
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
from openai import OpenAI

from core.chapter_parser import split_into_chapters, sanitize_title_for_filename, clean_text
from core.advanced_chunker import chunk_chapter_advanced

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False


class SingleVoicePipeline:
    """
    Full-book audiobook generation pipeline using OpenAI TTS.

    Based on husband's generate_full_book.py implementation.
    """

    def __init__(
        self,
        api_key: str,
        model_name: str = "gpt-4o-mini-tts",
        voice_name: str = "sage",
        max_words_per_chunk: int = 500,
        max_chars_per_chunk: int = 3500
    ):
        """
        Initialize the single voice pipeline.

        Note: OpenAI TTS has a strict 4096 char / 2000 token limit.
        We use conservative defaults (3500 chars, 500 words) to stay safe.
        """
        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name
        self.voice_name = voice_name
        self.max_words = max_words_per_chunk
        self.max_chars = max_chars_per_chunk

    def generate_audio_chunk(self, text: str, output_path: Path) -> bool:
        """
        Generate audio from text using OpenAI TTS API.
        Returns True if successful, False otherwise.
        """
        try:
            print(f"   🎙️ Generating audio: {output_path.name}")

            response = self.client.audio.speech.create(
                model=self.model_name,
                voice=self.voice_name,
                input=text
            )

            # Read audio bytes
            audio_bytes = response.read()

            # Write to file
            with open(output_path, "wb") as f:
                f.write(audio_bytes)

            print(f"   ✅ Saved: {output_path.name}")
            return True

        except Exception as e:
            print(f"   ❌ Failed to generate {output_path.name}: {e}")
            return False

    def merge_chunks_pydub(self, chunk_paths: List[Path], final_path: Path) -> bool:
        """
        Merge MP3 chunks using pydub.
        Returns True if successful.
        """
        if not PYDUB_AVAILABLE:
            print("   ❌ pydub not available for merging")
            return False

        if not chunk_paths:
            print("   ❌ No chunks to merge")
            return False

        if len(chunk_paths) == 1:
            # Single chunk, just copy
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

    def generate_chapter(
        self,
        chapter: Dict,
        output_dir: Path
    ) -> Optional[Path]:
        """
        Generate audio for a single chapter.

        Args:
            chapter: Dict with "index", "title", "text"
            output_dir: Directory to save output files

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

            if self.generate_audio_chunk(chunk, chunk_path):
                chunk_paths.append(chunk_path)
            else:
                print(f"   ⚠️ Failed chunk {i}/{len(chunks)}")

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

    def generate_full_book(
        self,
        book_text: str,
        output_dir: Path,
        book_title: str = "Audiobook"
    ) -> List[Path]:
        """
        Generate audiobook for entire book.

        Args:
            book_text: Full book text
            output_dir: Directory to save output files
            book_title: Title for the final merged audiobook file

        Returns:
            List of paths to audio files (chapters + final merged file as last item)
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        print("=" * 60)
        print("📘 Starting Full Book Generation (Single Voice)")
        print("=" * 60)

        # Split into chapters
        chapters = split_into_chapters(book_text)
        print(f"\nℹ️ Found {len(chapters)} chapter(s)")

        if not chapters:
            print("❌ No chapters found!")
            return []

        # Generate each chapter
        chapter_paths = []
        for chapter in chapters:
            final_path = self.generate_chapter(chapter, output_dir)
            if final_path:
                chapter_paths.append(final_path)

        if not chapter_paths:
            print("❌ No chapters generated!")
            return []

        # Merge all chapters into final audiobook
        safe_title = sanitize_title_for_filename(book_title)
        final_book_path = output_dir / f"{safe_title}_COMPLETE.mp3"

        print(f"\n📚 Merging {len(chapter_paths)} chapters into final audiobook...")
        if self.merge_chunks_pydub(chapter_paths, final_book_path):
            print(f"✅ Final audiobook: {final_book_path.name}")
        else:
            print("⚠️ Could not merge chapters, using last chapter as output")
            final_book_path = chapter_paths[-1]

        print("\n" + "=" * 60)
        print(f"✅ Book Generation Complete!")
        print(f"   Generated {len(chapter_paths)}/{len(chapters)} chapters")
        print(f"   Output: {output_dir}")
        print("=" * 60)

        # Return all chapter paths plus the final merged file
        return chapter_paths + [final_book_path]


def generate_single_voice_audiobook(
    manuscript_text: str,
    output_dir: Path,
    api_key: str,
    voice_id: str,
    tts_provider: str = "openai",
    book_title: str = "Audiobook"
) -> List[Path]:
    """
    Convenience function to generate a single-voice audiobook.

    Args:
        manuscript_text: Full book text
        output_dir: Directory to save output files
        api_key: API key for the TTS provider
        voice_id: Voice ID to use for narration
        tts_provider: TTS provider (currently only 'openai' supported)
        book_title: Title for the final merged audiobook file

    Returns:
        List of paths to generated audio files (final merged file is last)
    """
    if tts_provider != "openai":
        raise ValueError(f"Single voice pipeline currently only supports OpenAI, got: {tts_provider}")

    pipeline = SingleVoicePipeline(
        api_key=api_key,
        voice_name=voice_id,
    )

    return pipeline.generate_full_book(manuscript_text, output_dir, book_title)
