"""
Phoenix & Peacock Dual-Voice Pipeline
Character-aware audiobook generation with distinct voices for narrator and characters
Integrated from husband's generate_dualvoice_ch1.py
"""

import os
import time
from pathlib import Path
from typing import List, Dict, Optional

try:
    from elevenlabs.client import ElevenLabs
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

from core.chapter_parser import clean_text, detect_character_dialogue


class DualVoicePipeline:
    """
    Dual-voice audiobook generation pipeline using ElevenLabs.

    Phoenix (Narrator): Warm, mature storyteller voice
    Peacock (Character): Distinct character voice for dialogue

    Based on husband's generate_dualvoice_ch1.py implementation.
    """

    def __init__(
        self,
        api_key: str,
        narrator_voice_id: str,
        character_voice_id: str,
        character_name: str = "Vihan",
        model_id: str = "eleven_multilingual_v2",
        output_format: str = "mp3_44100_128"
    ):
        if not ELEVENLABS_AVAILABLE:
            raise ImportError("ElevenLabs SDK not available. Install with: pip install elevenlabs")

        self.client = ElevenLabs(api_key=api_key)
        self.narrator_voice_id = narrator_voice_id  # Phoenix
        self.character_voice_id = character_voice_id  # Peacock
        self.character_name = character_name
        self.model_id = model_id
        self.output_format = output_format

    def generate_tts(
        self,
        text: str,
        voice_id: str,
        output_path: Path,
        retries: int = 3
    ) -> bool:
        """
        Generate TTS audio using ElevenLabs API.
        Returns True if successful, False otherwise.

        From husband's tts() function in generate_dualvoice_ch1.py
        """
        for attempt in range(retries):
            try:
                audio_stream = self.client.text_to_speech.convert(
                    voice_id=voice_id,
                    model_id=self.model_id,
                    output_format=self.output_format,
                    text=text
                )

                # Collect audio data
                audio_data = b""
                for chunk in audio_stream:
                    if isinstance(chunk, bytes):
                        audio_data += chunk
                    else:
                        raise ValueError("JSON error chunk (likely API error)")

                # Validate MP3 header
                if not (audio_data.startswith(b"ID3") or audio_data.startswith(b"\xff")):
                    raise ValueError("Invalid MP3 header - ElevenLabs returned error JSON")

                # Write to file
                with open(output_path, "wb") as f:
                    f.write(audio_data)

                return True

            except Exception as e:
                print(f"   ⚠️ TTS error (attempt {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    time.sleep(1)  # Wait before retry

        return False

    def assemble_dual_voice(
        self,
        audio_parts: List[Path],
        output_path: Path,
        silence_ms: int = 200
    ) -> bool:
        """
        Combine narrator + character audio segments in proper order.
        Adds silence between parts for natural pacing.

        From husband's assemble() function in generate_dualvoice_ch1.py

        Args:
            audio_parts: List of audio file paths in order
            output_path: Path to final output file
            silence_ms: Milliseconds of silence between parts

        Returns:
            True if successful, False otherwise
        """
        if not PYDUB_AVAILABLE:
            print("   ❌ pydub not available for assembly")
            return False

        if not audio_parts:
            print("   ❌ No audio parts to assemble")
            return False

        try:
            print(f"   🔄 Assembling {len(audio_parts)} audio parts...")

            # Start with brief silence
            final_audio = AudioSegment.silent(duration=silence_ms)

            for part_path in audio_parts:
                if not part_path.exists():
                    print(f"   ⚠️ Part not found: {part_path}")
                    continue

                segment = AudioSegment.from_mp3(str(part_path))
                final_audio += segment
                final_audio += AudioSegment.silent(duration=silence_ms)

            # Export final audio
            final_audio.export(str(output_path), format="mp3", bitrate="128k")
            print(f"   ✅ Assembled: {output_path.name}")
            return True

        except Exception as e:
            print(f"   ❌ Assembly failed: {e}")
            return False

    def generate_chapter_dual_voice(
        self,
        chapter_text: str,
        output_dir: Path,
        chapter_number: int = 1
    ) -> Optional[Path]:
        """
        Generate dual-voice audio for a single chapter.

        Args:
            chapter_text: Chapter text (without header)
            output_dir: Directory to save output files
            chapter_number: Chapter number (for filename)

        Returns:
            Path to final dual-voice audio file, or None if failed
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        temp_dir = output_dir / "temp_dual"
        temp_dir.mkdir(exist_ok=True)

        print(f"\n🎭 Generating Dual-Voice Chapter {chapter_number}")
        print(f"   Narrator: Phoenix | Character ({self.character_name}): Peacock")

        # Clean text
        text = clean_text(chapter_text)

        # Split into narrator and character parts
        parts = detect_character_dialogue(text, self.character_name)
        print(f"   Found {len(parts)} dialogue segments")

        # Generate audio for each part
        audio_files = []

        for i, part in enumerate(parts, start=1):
            speaker = part["speaker"]
            block_text = part["text"]

            # Choose voice
            voice_id = self.character_voice_id if speaker == "character" else self.narrator_voice_id
            voice_label = "Peacock" if speaker == "character" else "Phoenix"

            # Output filename
            temp_filename = f"ch{chapter_number}_part_{i}_{speaker}.mp3"
            temp_path = temp_dir / temp_filename

            print(f"   🎤 [{voice_label}] Part {i}/{len(parts)}")

            if self.generate_tts(block_text, voice_id, temp_path):
                audio_files.append(temp_path)
            else:
                print(f"   ❌ Failed to generate part {i}")

        if not audio_files:
            print(f"   ❌ No audio generated for Chapter {chapter_number}")
            return None

        # Assemble all parts
        final_filename = f"CHAPTER_{chapter_number:02d}_DUAL_VOICE.mp3"
        final_path = output_dir / final_filename

        if self.assemble_dual_voice(audio_files, final_path):
            print(f"   ✅ Chapter {chapter_number} complete!")
            return final_path
        else:
            print(f"   ⚠️ Assembly failed, but individual parts saved")
            return None


def generate_dual_voice_audiobook(
    manuscript_text: str,
    output_dir,
    api_key: str,
    narrator_voice_id: str,
    character_voice_id: str,
    character_name: str,
) -> list:
    """
    Convenience function to generate a dual-voice audiobook.

    Args:
        manuscript_text: Full book text
        output_dir: Directory to save output files
        api_key: ElevenLabs API key
        narrator_voice_id: Voice ID for narrator
        character_voice_id: Voice ID for character
        character_name: Name of the character

    Returns:
        List of paths to generated audio files
    """
    from pathlib import Path

    output_dir = Path(output_dir)

    pipeline = DualVoicePipeline(
        api_key=api_key,
        narrator_voice_id=narrator_voice_id,
        character_voice_id=character_voice_id,
        character_name=character_name,
    )

    # Generate chapter by chapter
    # For now, treat entire text as one chapter
    result = pipeline.generate_chapter_dual_voice(manuscript_text, output_dir, chapter_number=1)

    return [result] if result else []
