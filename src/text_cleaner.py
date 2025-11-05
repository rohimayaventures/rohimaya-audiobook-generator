# src/text_cleaner.py
import re

def clean_text(text: str) -> str:
    """
    Cleans text by removing emojis, special symbols, and non-speech characters
    to ensure smooth TTS generation.

    Args:
        text (str): Raw input text.
    Returns:
        str: Cleaned text safe for TTS.
    """
    # Remove emojis and other pictographs
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002700-\U000027BF"  # dingbats
        "\U000024C2-\U0001F251"  # enclosed characters
        "]+",
        flags=re.UNICODE,
    )
    text = emoji_pattern.sub(r"", text)

    # Remove stray control characters and extra whitespace
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s{2,}", " ", text)

    # Remove weird non-breaking spaces and invisible characters
    text = text.replace("\xa0", " ").replace("\u200b", "")

    return text.strip()