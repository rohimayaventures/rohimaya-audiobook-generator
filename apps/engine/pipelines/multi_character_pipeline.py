"""
Multi-Character Voice Pipeline

Advanced audiobook generation with:
- Multiple character voices (auto-detected or user-specified)
- Emotional TTS instructions per segment
- Dynamic voice switching for dialogue
- Narrator voice for non-dialogue text

Uses OpenAI gpt-4o-mini-tts which supports emotional instructions
via the 'instructions' parameter.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from openai import OpenAI

from agents.emotion_parser_agent import (
    analyze_text_for_emotions_and_characters,
    extract_characters_from_manuscript,
    build_emotional_tts_instruction,
    EmotionalTone,
)
from core.chapter_parser import split_into_chapters, sanitize_title_for_filename, clean_text
from core.advanced_chunker import chunk_chapter_advanced

logger = logging.getLogger(__name__)

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    logger.warning("pydub not available - audio merging disabled")


@dataclass
class VoiceAssignment:
    """Voice assignment for a character or narrator"""
    name: str
    voice_id: str
    provider: str = "openai"
    is_narrator: bool = False


class MultiCharacterPipeline:
    """
    Multi-character audiobook generation pipeline.

    Supports:
    - Automatic character detection and voice assignment
    - Emotional TTS instructions
    - Dynamic voice switching for dialogue
    """

    def __init__(
        self,
        api_key: str,
        model_name: str = "gpt-4o-mini-tts",
        narrator_voice: str = "fable",
        analysis_model: str = "gpt-4o-mini",
        max_words_per_chunk: int = 700,
        max_chars_per_chunk: int = 4000,  # OpenAI TTS limit
    ):
        """
        Initialize the multi-character pipeline.

        Args:
            api_key: OpenAI API key
            model_name: TTS model (gpt-4o-mini-tts supports emotional instructions)
            narrator_voice: Default narrator voice ID
            analysis_model: Model for text analysis
            max_words_per_chunk: Maximum words per TTS chunk
            max_chars_per_chunk: Maximum characters per TTS call
        """
        self.client = OpenAI(api_key=api_key)
        self.api_key = api_key
        self.model_name = model_name
        self.narrator_voice = narrator_voice
        self.analysis_model = analysis_model
        self.max_words = max_words_per_chunk
        self.max_chars = max_chars_per_chunk

        # Voice assignments (character name -> VoiceAssignment)
        self.voice_assignments: Dict[str, VoiceAssignment] = {}

        # Set up narrator
        self.voice_assignments["__narrator__"] = VoiceAssignment(
            name="Narrator",
            voice_id=narrator_voice,
            provider="openai",
            is_narrator=True,
        )

    def set_narrator_voice(self, voice_id: str):
        """Set the narrator voice."""
        self.narrator_voice = voice_id
        self.voice_assignments["__narrator__"] = VoiceAssignment(
            name="Narrator",
            voice_id=voice_id,
            provider="openai",
            is_narrator=True,
        )

    def assign_character_voice(
        self,
        character_name: str,
        voice_id: str,
        provider: str = "openai",
    ):
        """
        Assign a specific voice to a character.

        Args:
            character_name: Character name (case-insensitive)
            voice_id: Voice ID for this character
            provider: TTS provider
        """
        self.voice_assignments[character_name.lower()] = VoiceAssignment(
            name=character_name,
            voice_id=voice_id,
            provider=provider,
        )

    def auto_assign_voices(
        self,
        manuscript_structure: Dict[str, Any],
        max_character_voices: int = 4,
    ):
        """
        Automatically detect characters and assign voices.

        Args:
            manuscript_structure: Parsed manuscript from manuscript_parser_agent
            max_character_voices: Maximum number of distinct character voices
        """
        characters = extract_characters_from_manuscript(
            manuscript_structure=manuscript_structure,
            api_key=self.api_key,
            model=self.analysis_model,
        )

        # Assign voices to top N characters by dialogue count
        for char in characters[:max_character_voices]:
            voice_rec = char.get("voice_recommendation", {})
            self.voice_assignments[char["name"].lower()] = VoiceAssignment(
                name=char["name"],
                voice_id=voice_rec.get("voice_id", "alloy"),
                provider=voice_rec.get("provider", "openai"),
            )
            logger.info(f"Auto-assigned voice '{voice_rec.get('voice_id')}' to character '{char['name']}'")

    def get_voice_for_speaker(self, speaker: Optional[str]) -> VoiceAssignment:
        """
        Get voice assignment for a speaker.

        Args:
            speaker: Speaker name or None for narrator

        Returns:
            VoiceAssignment for the speaker
        """
        if speaker is None:
            return self.voice_assignments["__narrator__"]

        speaker_lower = speaker.lower()
        if speaker_lower in self.voice_assignments:
            return self.voice_assignments[speaker_lower]

        # Check aliases
        for name, assignment in self.voice_assignments.items():
            if speaker_lower in name or name in speaker_lower:
                return assignment

        # Default to narrator for unknown speakers
        return self.voice_assignments["__narrator__"]

    def generate_audio_segment(
        self,
        text: str,
        output_path: Path,
        voice_id: str,
        emotion: str = "neutral",
        segment_type: str = "narration",
    ) -> bool:
        """
        Generate audio for a text segment with emotional TTS.

        Args:
            text: Text to convert to speech
            output_path: Output audio file path
            voice_id: OpenAI voice ID
            emotion: Emotional tone
            segment_type: Type of segment (narration/dialogue/internal_thought)

        Returns:
            True if successful
        """
        try:
            # Build emotional instruction
            instruction = build_emotional_tts_instruction(emotion, segment_type)

            logger.debug(f"Generating audio: voice={voice_id}, emotion={emotion}")
            logger.debug(f"Instruction: {instruction}")

            # Use gpt-4o-mini-tts with instructions
            response = self.client.audio.speech.create(
                model=self.model_name,
                voice=voice_id,
                input=text,
                instructions=instruction,
            )

            # Save audio
            audio_bytes = response.read()
            with open(output_path, "wb") as f:
                f.write(audio_bytes)

            return True

        except Exception as e:
            logger.error(f"Failed to generate audio segment: {e}")
            return False

    def generate_chapter_multi_voice(
        self,
        chapter: Dict[str, Any],
        output_dir: Path,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> Optional[Path]:
        """
        Generate audio for a chapter using multiple voices and emotions.

        Args:
            chapter: Chapter dict with index, title, text
            output_dir: Directory to save output files
            progress_callback: Optional progress callback

        Returns:
            Path to final chapter audio file, or None if failed
        """
        idx = chapter.get("index", 1)
        title = chapter.get("title", f"Chapter {idx}")
        text = clean_text(chapter.get("text", ""))

        if not text.strip():
            logger.warning(f"Skipping empty Chapter {idx}")
            return None

        logger.info(f"Processing Chapter {idx}: {title}")
        logger.info(f"  Length: {len(text)} chars, ~{len(text.split())} words")

        # Analyze chapter for emotions and character dialogue
        analysis = analyze_text_for_emotions_and_characters(
            text=text,
            api_key=self.api_key,
            model=self.analysis_model,
            known_characters=list(self.voice_assignments.keys()),
        )

        segments = analysis.get("segments", [])
        if not segments:
            # Fallback to single segment
            segments = [{
                "text": text,
                "speaker": None,
                "emotion": "neutral",
                "segment_type": "narration",
            }]

        logger.info(f"  Found {len(segments)} segments")

        # Generate audio for each segment
        segment_paths = []
        safe_title = sanitize_title_for_filename(title)

        for i, segment in enumerate(segments):
            segment_text = segment.get("text", "").strip()
            if not segment_text:
                continue

            # Get voice for this segment
            speaker = segment.get("speaker")
            voice_assignment = self.get_voice_for_speaker(speaker)

            # Handle text chunking if needed
            if len(segment_text) > self.max_chars:
                # Split long segments
                text_chunks = self._split_text_for_tts(segment_text)
            else:
                text_chunks = [segment_text]

            for chunk_idx, chunk_text in enumerate(text_chunks):
                segment_filename = f"Chapter_{idx:02d}_{safe_title}_seg{i:03d}_chunk{chunk_idx}.mp3"
                segment_path = output_dir / segment_filename

                success = self.generate_audio_segment(
                    text=chunk_text,
                    output_path=segment_path,
                    voice_id=voice_assignment.voice_id,
                    emotion=segment.get("emotion", "neutral"),
                    segment_type=segment.get("segment_type", "narration"),
                )

                if success:
                    segment_paths.append(segment_path)

            if progress_callback:
                progress = (i + 1) / len(segments) * 100
                progress_callback(progress, f"Chapter {idx}: {i+1}/{len(segments)} segments")

        if not segment_paths:
            logger.error(f"No audio generated for Chapter {idx}")
            return None

        # Merge all segments into final chapter file
        final_filename = f"Chapter_{idx:02d}_{safe_title}_FINAL.mp3"
        final_path = output_dir / final_filename

        if self._merge_audio_segments(segment_paths, final_path):
            logger.info(f"Chapter {idx} complete: {final_path.name}")

            # Clean up segment files
            for seg_path in segment_paths:
                try:
                    seg_path.unlink()
                except:
                    pass

            return final_path
        else:
            logger.warning(f"Merge failed for Chapter {idx}, returning last segment")
            return segment_paths[-1] if segment_paths else None

    def _split_text_for_tts(self, text: str) -> List[str]:
        """
        Split text into chunks suitable for TTS API.

        Args:
            text: Text to split

        Returns:
            List of text chunks
        """
        chunks = []
        current_chunk = ""

        # Split by sentences
        sentences = text.replace('\n', ' ').split('. ')

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Add period back
            if not sentence.endswith(('.', '!', '?', '"')):
                sentence += '.'

            if len(current_chunk) + len(sentence) + 1 > self.max_chars:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk = current_chunk + ' ' + sentence if current_chunk else sentence

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _merge_audio_segments(self, segment_paths: List[Path], output_path: Path) -> bool:
        """
        Merge multiple audio segments into one file.

        Args:
            segment_paths: List of audio file paths
            output_path: Output file path

        Returns:
            True if successful
        """
        if not PYDUB_AVAILABLE:
            logger.warning("pydub not available, cannot merge segments")
            # Copy last segment as output
            if segment_paths:
                import shutil
                shutil.copy(segment_paths[-1], output_path)
                return True
            return False

        if not segment_paths:
            return False

        if len(segment_paths) == 1:
            import shutil
            shutil.copy(segment_paths[0], output_path)
            return True

        try:
            combined = AudioSegment.empty()
            for path in segment_paths:
                if path.exists():
                    audio = AudioSegment.from_mp3(str(path))
                    combined += audio

            combined.export(str(output_path), format="mp3", bitrate="192k")
            return True

        except Exception as e:
            logger.error(f"Failed to merge audio segments: {e}")
            return False

    def generate_full_book(
        self,
        manuscript_structure: Dict[str, Any],
        output_dir: Path,
        book_title: str = "Audiobook",
        auto_assign_voices: bool = True,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> List[Path]:
        """
        Generate full multi-character audiobook.

        Args:
            manuscript_structure: Parsed manuscript from manuscript_parser_agent
            output_dir: Directory to save output files
            book_title: Title for the final audiobook
            auto_assign_voices: Whether to auto-assign voices to characters
            progress_callback: Optional progress callback

        Returns:
            List of paths to audio files (chapters + final merged)
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info("=" * 60)
        logger.info("Starting Multi-Character Audiobook Generation")
        logger.info("=" * 60)

        # Auto-assign voices if requested
        if auto_assign_voices:
            logger.info("Auto-assigning character voices...")
            self.auto_assign_voices(manuscript_structure)

        # Log voice assignments
        logger.info(f"Voice assignments ({len(self.voice_assignments)}):")
        for name, assignment in self.voice_assignments.items():
            logger.info(f"  {assignment.name}: {assignment.voice_id}")

        chapters = manuscript_structure.get("chapters", [])
        if not chapters:
            logger.error("No chapters found in manuscript")
            return []

        logger.info(f"Processing {len(chapters)} chapters")

        # Generate each chapter
        chapter_paths = []
        for i, chapter in enumerate(chapters):
            if progress_callback:
                progress = (i / len(chapters)) * 90  # 90% for chapter generation
                progress_callback(progress, f"Processing chapter {i+1}/{len(chapters)}")

            chapter_path = self.generate_chapter_multi_voice(
                chapter=chapter,
                output_dir=output_dir,
            )

            if chapter_path:
                chapter_paths.append(chapter_path)

        if not chapter_paths:
            logger.error("No chapters generated")
            return []

        # Merge all chapters into final audiobook
        if progress_callback:
            progress_callback(95, "Merging chapters into final audiobook")

        safe_title = sanitize_title_for_filename(book_title)
        final_path = output_dir / f"{safe_title}_COMPLETE.mp3"

        logger.info(f"Merging {len(chapter_paths)} chapters into final audiobook...")

        if self._merge_audio_segments(chapter_paths, final_path):
            logger.info(f"Final audiobook: {final_path.name}")
        else:
            logger.warning("Could not merge chapters")
            final_path = chapter_paths[-1]

        if progress_callback:
            progress_callback(100, "Complete")

        logger.info("=" * 60)
        logger.info("Multi-Character Audiobook Complete!")
        logger.info(f"  Generated {len(chapter_paths)}/{len(chapters)} chapters")
        logger.info(f"  Output: {output_dir}")
        logger.info("=" * 60)

        return chapter_paths + [final_path]


def generate_multi_character_audiobook(
    manuscript_text: str,
    output_dir: Path,
    api_key: str,
    narrator_voice_id: str,
    character_voices: Optional[Dict[str, str]] = None,
    book_title: str = "Audiobook",
    progress_callback: Optional[Callable[[float, str], None]] = None,
) -> List[Path]:
    """
    Convenience function to generate a multi-character audiobook.

    Args:
        manuscript_text: Full manuscript text
        output_dir: Directory to save output files
        api_key: OpenAI API key
        narrator_voice_id: Voice ID for narrator
        character_voices: Optional dict mapping character names to voice IDs
        book_title: Title for the audiobook
        progress_callback: Optional progress callback

    Returns:
        List of paths to generated audio files
    """
    from agents.manuscript_parser_agent import parse_manuscript_structure

    # Parse manuscript
    manuscript_structure = parse_manuscript_structure(
        manuscript_text=manuscript_text,
        api_key=api_key,
    )

    # Create pipeline
    pipeline = MultiCharacterPipeline(
        api_key=api_key,
        narrator_voice=narrator_voice_id,
    )

    # Assign character voices if provided
    if character_voices:
        for char_name, voice_id in character_voices.items():
            pipeline.assign_character_voice(char_name, voice_id)

    # Generate audiobook
    return pipeline.generate_full_book(
        manuscript_structure=manuscript_structure,
        output_dir=output_dir,
        book_title=book_title,
        auto_assign_voices=character_voices is None,  # Auto-assign if none provided
        progress_callback=progress_callback,
    )
