"""
Advanced Text Chunker - Smarter chunking for TTS with word/char limits
Integrated from husband's Peacock/Phoenix implementation
"""

import re
from typing import List


def chunk_chapter_advanced(
    text: str,
    max_words: int = 500,
    max_chars: int = 3500
) -> List[str]:
    """
    Split chapter text into chunks that stay under token limits.
    Uses BOTH word count and character count for safety.
    Preserves sentence boundaries whenever possible.

    Algorithm from husband's generate_full_book.py (lines 125-225)

    IMPORTANT: OpenAI TTS has a strict 4096 character / 2000 token limit.
    We use conservative defaults (3500 chars, 500 words) to stay well under.

    Args:
        text: Chapter text to chunk
        max_words: Maximum words per chunk (default: 500 ~ 650 tokens)
        max_chars: Maximum characters per chunk (default: 3500 - safe for OpenAI TTS)

    Returns:
        List of text chunks
    """
    # Split into sentences first
    sentences = re.split(r'([.!?]+[\s\n]+)', text)

    # Rejoin sentences with their punctuation
    sentences_list = []
    i = 0
    while i < len(sentences):
        if i + 1 < len(sentences):
            sentences_list.append(sentences[i] + sentences[i + 1])
            i += 2
        else:
            sentences_list.append(sentences[i])
            i += 1

    chunks = []
    current_chunk = ""
    current_word_count = 0
    current_char_count = 0

    for sentence in sentences_list:
        sentence_word_count = len(sentence.split())
        sentence_char_count = len(sentence)

        # If single sentence exceeds both limits, split by words
        if sentence_word_count > max_words or sentence_char_count > max_chars:
            # Flush current chunk first
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
                current_chunk = ""
                current_word_count = 0
                current_char_count = 0

            # Split long sentence - use smaller size to be safe
            words = sentence.split()
            split_size = min(max_words, 600)  # Extra conservative
            for word_idx in range(0, len(words), split_size):
                chunk_words = words[word_idx:word_idx + split_size]
                chunk_text = " ".join(chunk_words)

                # Double-check character limit
                if len(chunk_text) > max_chars:
                    # Split further by character count if needed
                    for char_idx in range(0, len(chunk_text), max_chars):
                        chunks.append(chunk_text[char_idx:char_idx + max_chars].strip())
                else:
                    chunks.append(chunk_text)
            continue

        # Check if adding this sentence would exceed limits (check both)
        would_exceed_words = current_word_count + sentence_word_count > max_words
        would_exceed_chars = current_char_count + sentence_char_count > max_chars

        if would_exceed_words or would_exceed_chars:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
                current_chunk = sentence
                current_word_count = sentence_word_count
                current_char_count = sentence_char_count
            else:
                # Edge case: single sentence that's too large, split it
                if sentence_char_count > max_chars:
                    # Split by character count
                    for j in range(0, len(sentence), max_chars):
                        chunks.append(sentence[j:j + max_chars].strip())
                else:
                    chunks.append(sentence.strip())
                current_word_count = 0
                current_char_count = 0
        else:
            # Add sentence to current chunk
            if current_chunk:
                current_chunk += " " + sentence
            else:
                current_chunk = sentence
            current_word_count += sentence_word_count
            current_char_count += sentence_char_count

    # Add final chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    # Final safety check: ensure no chunk exceeds limits
    final_chunks = []
    for chunk in chunks:
        chunk_words = len(chunk.split())
        chunk_chars = len(chunk)

        if chunk_words > max_words or chunk_chars > max_chars:
            # Split further if needed
            words = chunk.split()
            split_size = min(max_words, 600)  # Extra conservative
            for word_idx in range(0, len(words), split_size):
                final_chunks.append(" ".join(words[word_idx:word_idx + split_size]))
        else:
            final_chunks.append(chunk)

    return final_chunks if final_chunks else [text]


def chunk_simple(text: str, max_chars: int = 8000) -> List[str]:
    """
    Simpler chunking by paragraph breaks.
    From husband's generate_chapters.py

    Args:
        text: Text to chunk
        max_chars: Maximum characters per chunk

    Returns:
        List of text chunks
    """
    chunks = []
    text = text.strip()

    while len(text) > max_chars:
        # Try to split at paragraph break
        split_at = text.rfind("\n\n", 0, max_chars)
        if split_at == -1:
            # No paragraph break found, just split at max_chars
            split_at = max_chars

        chunks.append(text[:split_at].strip())
        text = text[split_at:].strip()

    chunks.append(text)
    return chunks
