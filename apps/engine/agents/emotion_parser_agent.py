"""
Emotion and Character Parser Agent

Uses OpenAI to analyze manuscript text and extract:
- Character names and dialogue attribution
- Emotional tone of each paragraph/section
- Speaker identification for multi-voice narration

This enables:
- Multi-character voice casting
- Emotional TTS instructions
- Dynamic voice switching during narration
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from openai import OpenAI

logger = logging.getLogger(__name__)


class EmotionalTone(str, Enum):
    """Standard emotional tones for TTS instructions"""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    FEARFUL = "fearful"
    EXCITED = "excited"
    TENDER = "tender"
    MYSTERIOUS = "mysterious"
    DRAMATIC = "dramatic"
    CONTEMPLATIVE = "contemplative"
    HUMOROUS = "humorous"
    TENSE = "tense"
    ROMANTIC = "romantic"
    WISTFUL = "wistful"


@dataclass
class DialogueLine:
    """A single line of dialogue with metadata"""
    text: str
    speaker: Optional[str]
    emotion: str
    is_dialogue: bool
    surrounding_text: str = ""


@dataclass
class TextSegment:
    """A segment of text with speaker and emotion metadata"""
    text: str
    speaker: Optional[str]  # None = narrator
    emotion: str
    segment_type: str  # "narration", "dialogue", "internal_thought"
    character_name: Optional[str] = None


@dataclass
class CharacterInfo:
    """Information about a detected character"""
    name: str
    aliases: List[str]
    gender: Optional[str]
    dialogue_count: int
    suggested_voice_type: str


# System prompt for character and emotion analysis
ANALYSIS_SYSTEM_PROMPT = """You are an expert literary analyst specializing in audiobook production. Your task is to analyze text and extract character and emotional information for multi-voice TTS narration.

Analyze the provided text and return a JSON object with:

{
  "characters": [
    {
      "name": "Character Name",
      "aliases": ["nicknames", "titles"],
      "gender": "male/female/unknown",
      "dialogue_count": 5,
      "personality_notes": "brief description",
      "suggested_voice_type": "deep male/young female/elderly/etc"
    }
  ],
  "segments": [
    {
      "text": "The exact text of this segment",
      "speaker": "CharacterName" or null for narrator,
      "emotion": "neutral/happy/sad/angry/fearful/excited/tender/mysterious/dramatic/contemplative/humorous/tense/romantic/wistful",
      "segment_type": "narration/dialogue/internal_thought"
    }
  ],
  "overall_tone": "The dominant emotional tone of the passage",
  "pov_character": "The point-of-view character if identifiable"
}

Rules:
1. Break text into segments at natural boundaries (dialogue, paragraph breaks, emotional shifts)
2. Identify speakers by dialogue tags ("he said", "she whispered", etc.)
3. Track character names and their variations/nicknames
4. Assess emotional tone based on context, word choice, and punctuation
5. Internal thoughts (often in italics or marked) should be tagged as the POV character
6. When speaker is ambiguous, mark as null (narrator will read)
7. Be conservative with emotion - default to "neutral" if unclear
"""


def analyze_text_for_emotions_and_characters(
    text: str,
    api_key: str,
    model: str = "gpt-4o-mini",
    known_characters: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Analyze text to extract characters, emotions, and speaker attribution.

    Args:
        text: Text to analyze (chapter or section)
        api_key: OpenAI API key
        model: OpenAI model to use
        known_characters: Optional list of known character names from earlier analysis

    Returns:
        Dictionary with characters, segments, overall_tone, pov_character
    """
    logger.info(f"Analyzing text for emotions/characters ({len(text)} chars)")

    client = OpenAI(api_key=api_key)

    # Truncate very long text
    max_chars = 30000  # ~7.5k tokens
    if len(text) > max_chars:
        logger.warning(f"Text too long ({len(text)} chars), truncating for analysis")
        text = text[:max_chars] + "\n\n[TEXT TRUNCATED]"

    # Add known characters to prompt if provided
    user_prompt = f"Analyze this text for character dialogue and emotional content:\n\n{text}"
    if known_characters:
        user_prompt = f"Known characters in this book: {', '.join(known_characters)}\n\n{user_prompt}"

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=8000,
            temperature=0.2,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)

        # Validate and normalize result
        result = _normalize_analysis_result(result)

        logger.info(
            f"Analysis complete: {len(result.get('characters', []))} characters, "
            f"{len(result.get('segments', []))} segments"
        )
        return result

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse OpenAI response as JSON: {e}")
        return _create_fallback_analysis(text)

    except Exception as e:
        logger.error(f"Error analyzing text: {e}")
        return _create_fallback_analysis(text)


def _normalize_analysis_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize and validate analysis result.

    Args:
        result: Raw result from OpenAI

    Returns:
        Normalized result with all fields guaranteed
    """
    # Ensure characters list
    characters = result.get("characters", [])
    if not isinstance(characters, list):
        characters = []

    normalized_characters = []
    for char in characters:
        if isinstance(char, dict) and char.get("name"):
            normalized_characters.append({
                "name": char.get("name"),
                "aliases": char.get("aliases", []),
                "gender": char.get("gender"),
                "dialogue_count": char.get("dialogue_count", 0),
                "personality_notes": char.get("personality_notes"),
                "suggested_voice_type": char.get("suggested_voice_type", "neutral"),
            })

    # Ensure segments list
    segments = result.get("segments", [])
    if not isinstance(segments, list):
        segments = []

    normalized_segments = []
    for seg in segments:
        if isinstance(seg, dict) and seg.get("text"):
            emotion = seg.get("emotion", "neutral").lower()
            # Validate emotion is in our enum
            try:
                emotion = EmotionalTone(emotion).value
            except ValueError:
                emotion = EmotionalTone.NEUTRAL.value

            normalized_segments.append({
                "text": seg.get("text", ""),
                "speaker": seg.get("speaker"),
                "emotion": emotion,
                "segment_type": seg.get("segment_type", "narration"),
            })

    return {
        "characters": normalized_characters,
        "segments": normalized_segments,
        "overall_tone": result.get("overall_tone", "neutral"),
        "pov_character": result.get("pov_character"),
    }


def _create_fallback_analysis(text: str) -> Dict[str, Any]:
    """
    Create fallback analysis using simple heuristics.

    Args:
        text: Original text

    Returns:
        Basic analysis result
    """
    logger.info("Using fallback analysis (heuristic-based)")

    # Simple dialogue detection using quotes
    segments = []
    characters = {}

    # Split into paragraphs
    paragraphs = text.split('\n\n')

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # Check for dialogue (text in quotes)
        dialogue_pattern = r'"([^"]+)"'
        dialogue_matches = re.findall(dialogue_pattern, para)

        if dialogue_matches:
            # Try to find speaker from dialogue tags
            speaker = _extract_speaker_from_context(para)
            if speaker:
                characters[speaker] = characters.get(speaker, 0) + 1

            segments.append({
                "text": para,
                "speaker": speaker,
                "emotion": _guess_emotion_from_text(para),
                "segment_type": "dialogue" if dialogue_matches else "narration",
            })
        else:
            segments.append({
                "text": para,
                "speaker": None,
                "emotion": _guess_emotion_from_text(para),
                "segment_type": "narration",
            })

    # Build character list
    character_list = [
        {
            "name": name,
            "aliases": [],
            "gender": None,
            "dialogue_count": count,
            "personality_notes": None,
            "suggested_voice_type": "neutral",
        }
        for name, count in characters.items()
    ]

    return {
        "characters": character_list,
        "segments": segments,
        "overall_tone": "neutral",
        "pov_character": None,
    }


def _extract_speaker_from_context(text: str) -> Optional[str]:
    """
    Try to extract speaker name from dialogue tags.

    Args:
        text: Text containing dialogue

    Returns:
        Speaker name or None
    """
    # Common dialogue tag patterns
    patterns = [
        r'"[^"]+"[,.]?\s*(?:said|asked|replied|whispered|shouted|exclaimed|murmured|called|answered|cried)\s+(\w+)',
        r'(\w+)\s+(?:said|asked|replied|whispered|shouted|exclaimed|murmured|called|answered|cried)[,.]?\s*"',
        r'"[^"]+"[,.]?\s*(\w+)\s+(?:said|asked|replied|whispered|shouted|exclaimed|murmured|called|answered|cried)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1)
            # Filter out common non-names
            if name.lower() not in ['he', 'she', 'they', 'i', 'the', 'a', 'an']:
                return name.capitalize()

    return None


def _guess_emotion_from_text(text: str) -> str:
    """
    Guess emotional tone from text using simple heuristics.

    Args:
        text: Text to analyze

    Returns:
        Emotion string
    """
    text_lower = text.lower()

    # Exclamation marks suggest excitement or anger
    if text.count('!') >= 2:
        if any(word in text_lower for word in ['no', 'stop', 'hate', 'angry']):
            return EmotionalTone.ANGRY.value
        return EmotionalTone.EXCITED.value

    # Question marks might indicate curiosity/confusion
    if text.count('?') >= 2:
        return EmotionalTone.CONTEMPLATIVE.value

    # Check for emotional keywords
    emotion_keywords = {
        EmotionalTone.SAD.value: ['sad', 'tears', 'cry', 'grief', 'sorrow', 'mourning', 'loss'],
        EmotionalTone.HAPPY.value: ['happy', 'joy', 'laugh', 'smile', 'delight', 'pleased'],
        EmotionalTone.ANGRY.value: ['angry', 'fury', 'rage', 'furious', 'hate', 'seething'],
        EmotionalTone.FEARFUL.value: ['fear', 'afraid', 'terror', 'panic', 'dread', 'scared'],
        EmotionalTone.ROMANTIC.value: ['love', 'kiss', 'embrace', 'heart', 'desire', 'passion'],
        EmotionalTone.MYSTERIOUS.value: ['strange', 'mysterious', 'shadow', 'secret', 'hidden'],
        EmotionalTone.TENSE.value: ['tension', 'nervous', 'anxious', 'worried', 'danger'],
    }

    for emotion, keywords in emotion_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            return emotion

    return EmotionalTone.NEUTRAL.value


def build_emotional_tts_instruction(emotion: str, segment_type: str = "narration") -> str:
    """
    Build TTS instruction string based on emotion and segment type.

    Args:
        emotion: Emotional tone
        segment_type: Type of segment (narration, dialogue, internal_thought)

    Returns:
        Instruction string for TTS system prompt
    """
    base_instructions = {
        EmotionalTone.NEUTRAL.value: "Read in a clear, measured tone.",
        EmotionalTone.HAPPY.value: "Read with warmth and a light, cheerful quality.",
        EmotionalTone.SAD.value: "Read with a softer, more subdued tone conveying melancholy.",
        EmotionalTone.ANGRY.value: "Read with intensity and sharp emphasis.",
        EmotionalTone.FEARFUL.value: "Read with tension and slight tremor in the voice.",
        EmotionalTone.EXCITED.value: "Read with energy and enthusiasm, slightly faster pace.",
        EmotionalTone.TENDER.value: "Read with gentleness and warmth, intimate quality.",
        EmotionalTone.MYSTERIOUS.value: "Read with a hushed, intriguing quality.",
        EmotionalTone.DRAMATIC.value: "Read with gravitas and dramatic emphasis.",
        EmotionalTone.CONTEMPLATIVE.value: "Read thoughtfully with measured pauses.",
        EmotionalTone.HUMOROUS.value: "Read with a light, playful tone.",
        EmotionalTone.TENSE.value: "Read with underlying tension, controlled urgency.",
        EmotionalTone.ROMANTIC.value: "Read with warmth and emotional intimacy.",
        EmotionalTone.WISTFUL.value: "Read with nostalgic longing, slightly dreamy.",
    }

    instruction = base_instructions.get(emotion, base_instructions[EmotionalTone.NEUTRAL.value])

    # Modify for segment type
    if segment_type == "dialogue":
        instruction += " Deliver as spoken dialogue with natural speech patterns."
    elif segment_type == "internal_thought":
        instruction += " Read as internal thoughts, slightly more introspective."

    return instruction


def get_voice_recommendation(character: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get voice recommendation for a character.

    Args:
        character: Character info dict

    Returns:
        Voice recommendation with provider/voice_id suggestions
    """
    gender = character.get("gender", "unknown")
    voice_type = character.get("suggested_voice_type", "").lower()

    # OpenAI voice recommendations
    openai_voices = {
        "male": {
            "deep": "onyx",
            "young": "echo",
            "warm": "fable",
            "default": "echo",
        },
        "female": {
            "soft": "shimmer",
            "young": "nova",
            "warm": "nova",
            "default": "nova",
        },
        "unknown": {
            "default": "alloy",
        },
    }

    gender_voices = openai_voices.get(gender, openai_voices["unknown"])

    # Try to match voice type
    voice_id = gender_voices.get("default")
    for key, vid in gender_voices.items():
        if key in voice_type:
            voice_id = vid
            break

    return {
        "provider": "openai",
        "voice_id": voice_id,
        "character_name": character.get("name"),
        "gender": gender,
        "notes": character.get("personality_notes"),
    }


def extract_characters_from_manuscript(
    manuscript_structure: Dict[str, Any],
    api_key: str,
    model: str = "gpt-4o-mini",
    max_chapters_to_analyze: int = 5,
) -> List[Dict[str, Any]]:
    """
    Extract all characters from a manuscript by analyzing early chapters.

    Args:
        manuscript_structure: Parsed manuscript from manuscript_parser_agent
        api_key: OpenAI API key
        model: OpenAI model
        max_chapters_to_analyze: Number of chapters to analyze

    Returns:
        List of character info dicts with voice recommendations
    """
    chapters = manuscript_structure.get("chapters", [])
    if not chapters:
        return []

    # Analyze first N chapters
    all_characters = {}

    for chapter in chapters[:max_chapters_to_analyze]:
        text = chapter.get("text", "")
        if not text:
            continue

        analysis = analyze_text_for_emotions_and_characters(
            text=text,
            api_key=api_key,
            model=model,
            known_characters=list(all_characters.keys()),
        )

        # Merge characters
        for char in analysis.get("characters", []):
            name = char.get("name")
            if name:
                if name in all_characters:
                    # Update dialogue count
                    all_characters[name]["dialogue_count"] += char.get("dialogue_count", 0)
                else:
                    all_characters[name] = char

    # Sort by dialogue count and add voice recommendations
    sorted_characters = sorted(
        all_characters.values(),
        key=lambda c: c.get("dialogue_count", 0),
        reverse=True,
    )

    # Add voice recommendations
    for char in sorted_characters:
        char["voice_recommendation"] = get_voice_recommendation(char)

    return sorted_characters
