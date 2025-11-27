"""
Cover Image Generator

Pluggable cover image generation system supporting multiple providers:
- OpenAI (DALL-E / GPT Image)
- NanoBanana (future)
- Other providers can be added

Environment variables:
- COVER_IMAGE_PROVIDER: "openai" or "nanobanana" (default: "openai")
- COVER_IMAGE_MODEL: Model to use (provider-specific)
- COVER_IMAGE_API_KEY: API key (uses OPENAI_API_KEY as fallback for OpenAI)
"""

import os
import logging
import base64
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Provider constants
PROVIDER_OPENAI = "openai"
PROVIDER_NANOBANANA = "nanobanana"

# Default models per provider
DEFAULT_MODELS = {
    PROVIDER_OPENAI: "dall-e-3",  # or "gpt-image-1" when available
    PROVIDER_NANOBANANA: "default",
}


def generate_cover_image(
    title: str,
    author: Optional[str],
    genre: Optional[str] = None,
    vibe: Optional[str] = None,
    aspect_ratio: str = "1:1",
    job_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate a cover image using the configured provider.

    Args:
        title: Book title
        author: Author name (optional)
        genre: Book genre (optional, helps with style)
        vibe: Desired visual vibe (e.g., "dark", "romantic", "mysterious")
        aspect_ratio: Image aspect ratio (default "1:1" for audiobook covers)
        job_id: Job ID for organizing storage

    Returns:
        {
            "provider": str,
            "model": str,
            "image_bytes": bytes,
            "width": int,
            "height": int,
            "prompt_used": str,
            "format": str  # "png" or "jpeg"
        }
    """
    # Get provider from environment
    provider = os.getenv("COVER_IMAGE_PROVIDER", PROVIDER_OPENAI).lower()

    logger.info(f"Generating cover image with provider: {provider}")
    logger.info(f"  Title: {title}")
    logger.info(f"  Author: {author}")
    logger.info(f"  Genre: {genre}")
    logger.info(f"  Vibe: {vibe}")

    if provider == PROVIDER_OPENAI:
        return _generate_openai_cover(title, author, genre, vibe, aspect_ratio)
    elif provider == PROVIDER_NANOBANANA:
        return _generate_nanobanana_cover(title, author, genre, vibe, aspect_ratio)
    else:
        logger.warning(f"Unknown provider '{provider}', falling back to OpenAI")
        return _generate_openai_cover(title, author, genre, vibe, aspect_ratio)


def _generate_openai_cover(
    title: str,
    author: Optional[str],
    genre: Optional[str],
    vibe: Optional[str],
    aspect_ratio: str
) -> Dict[str, Any]:
    """
    Generate cover image using OpenAI DALL-E or GPT Image API.

    Args:
        title: Book title
        author: Author name
        genre: Book genre
        vibe: Visual vibe
        aspect_ratio: Image aspect ratio

    Returns:
        Cover generation result
    """
    from openai import OpenAI

    # Get API key
    api_key = os.getenv("COVER_IMAGE_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("No API key found for cover generation. Set COVER_IMAGE_API_KEY or OPENAI_API_KEY")

    # Get model
    model = os.getenv("COVER_IMAGE_MODEL", DEFAULT_MODELS[PROVIDER_OPENAI])

    # Build prompt
    prompt = _build_cover_prompt(title, author, genre, vibe)

    logger.info(f"Using OpenAI model: {model}")
    logger.debug(f"Cover prompt: {prompt}")

    # Map aspect ratio to size
    size_map = {
        "1:1": "1024x1024",
        "16:9": "1792x1024",
        "9:16": "1024x1792",
    }
    size = size_map.get(aspect_ratio, "1024x1024")

    # Generate image
    client = OpenAI(api_key=api_key)

    try:
        response = client.images.generate(
            model=model,
            prompt=prompt,
            n=1,
            size=size,
            response_format="b64_json",
            quality="hd" if model == "dall-e-3" else "standard",
        )

        # Get image data
        image_data = response.data[0]
        image_b64 = image_data.b64_json
        image_bytes = base64.b64decode(image_b64)

        # Parse dimensions from size
        width, height = map(int, size.split("x"))

        return {
            "provider": PROVIDER_OPENAI,
            "model": model,
            "image_bytes": image_bytes,
            "width": width,
            "height": height,
            "prompt_used": prompt,
            "format": "png",
            "revised_prompt": getattr(image_data, "revised_prompt", None)
        }

    except Exception as e:
        logger.error(f"OpenAI cover generation failed: {e}")
        raise


def _generate_nanobanana_cover(
    title: str,
    author: Optional[str],
    genre: Optional[str],
    vibe: Optional[str],
    aspect_ratio: str
) -> Dict[str, Any]:
    """
    Generate cover image using NanoBanana API.

    TODO: Implement when NanoBanana integration is needed.

    This is a placeholder that shows where NanoBanana API calls would go.
    The expected flow:
    1. Get COVER_IMAGE_API_KEY for NanoBanana auth
    2. Build prompt using _build_cover_prompt()
    3. Make API call to NanoBanana endpoint
    4. Receive image bytes in response
    5. Return in same format as OpenAI generator

    Args:
        title: Book title
        author: Author name
        genre: Book genre
        vibe: Visual vibe
        aspect_ratio: Image aspect ratio

    Returns:
        Cover generation result

    Raises:
        NotImplementedError: NanoBanana integration not yet implemented
    """
    # TODO: NanoBanana API integration
    #
    # Expected implementation:
    #
    # api_key = os.getenv("COVER_IMAGE_API_KEY")
    # if not api_key:
    #     raise ValueError("COVER_IMAGE_API_KEY required for NanoBanana")
    #
    # model = os.getenv("COVER_IMAGE_MODEL", DEFAULT_MODELS[PROVIDER_NANOBANANA])
    # prompt = _build_cover_prompt(title, author, genre, vibe)
    #
    # # Make NanoBanana API call
    # response = requests.post(
    #     "https://api.nanobanana.com/v1/generate",  # Placeholder URL
    #     headers={"Authorization": f"Bearer {api_key}"},
    #     json={
    #         "prompt": prompt,
    #         "model": model,
    #         "width": 1024,
    #         "height": 1024,
    #         "format": "png"
    #     }
    # )
    #
    # if response.status_code != 200:
    #     raise RuntimeError(f"NanoBanana API error: {response.text}")
    #
    # image_bytes = response.content
    #
    # return {
    #     "provider": PROVIDER_NANOBANANA,
    #     "model": model,
    #     "image_bytes": image_bytes,
    #     "width": 1024,
    #     "height": 1024,
    #     "prompt_used": prompt,
    #     "format": "png"
    # }

    raise NotImplementedError(
        "NanoBanana cover generation not yet implemented. "
        "Set COVER_IMAGE_PROVIDER=openai to use OpenAI instead."
    )


def _build_cover_prompt(
    title: str,
    author: Optional[str],
    genre: Optional[str],
    vibe: Optional[str]
) -> str:
    """
    Build a prompt for cover image generation.

    Args:
        title: Book title
        author: Author name
        genre: Book genre
        vibe: Visual vibe

    Returns:
        Prompt string for image generation
    """
    # Base prompt
    prompt_parts = [
        "Professional audiobook cover art",
        "High quality digital illustration",
        "Cinematic composition",
        "Square aspect ratio (1:1)",
    ]

    # Add genre-specific styling
    genre_styles = {
        "romance": "romantic atmosphere, warm colors, intimate mood, elegant design",
        "thriller": "dark mood, suspenseful atmosphere, dramatic shadows, bold typography space",
        "mystery": "mysterious atmosphere, noir aesthetic, intriguing visual elements",
        "fantasy": "magical elements, ethereal lighting, epic fantasy aesthetic",
        "sci-fi": "futuristic elements, sci-fi aesthetic, technological themes",
        "horror": "dark atmosphere, gothic elements, unsettling mood",
        "literary": "sophisticated design, artistic composition, literary aesthetic",
        "self-help": "inspiring imagery, clean design, positive energy",
        "biography": "dignified composition, historical elements, sophisticated styling",
    }

    if genre and genre.lower() in genre_styles:
        prompt_parts.append(genre_styles[genre.lower()])

    # Add vibe if specified
    if vibe:
        prompt_parts.append(f"Visual mood: {vibe}")

    # Add brand styling
    prompt_parts.extend([
        "Premium quality suitable for audiobook platforms",
        "Dark, moody color palette with AuthorFlow Studios brand energy",
        "Leave appropriate space for title typography overlay",
        "Do NOT include any text in the image",
    ])

    # Add thematic hint from title
    prompt_parts.append(f"Inspired by the theme of a book titled: '{title}'")

    return ". ".join(prompt_parts)


def save_cover_to_file(
    cover_result: Dict[str, Any],
    output_path: Path
) -> Path:
    """
    Save generated cover to a file.

    Args:
        cover_result: Result from generate_cover_image()
        output_path: Where to save the image

    Returns:
        Path to saved file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "wb") as f:
        f.write(cover_result["image_bytes"])

    logger.info(f"Cover saved to: {output_path}")
    return output_path


def get_cover_filename(title: str, size: str = "2400x2400") -> str:
    """
    Generate a standard filename for the cover image.

    Args:
        title: Book title
        size: Image dimensions (default 2400x2400 for Findaway)

    Returns:
        Filename string
    """
    # Sanitize title for filename
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_title = safe_title.replace(' ', '_')[:50]  # Limit length

    if not safe_title:
        safe_title = "cover"

    return f"{safe_title}_cover_{size}.png"
