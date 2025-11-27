"""
Cover Image Generator

Pluggable cover image generation system supporting multiple providers:
- OpenAI (DALL-E 3)
- Banana.dev (SDXL / Flux models)
- Other providers can be added

Environment variables:
- COVER_IMAGE_PROVIDER: "openai" or "banana" (default: "openai")
- COVER_IMAGE_MODEL: Model to use (provider-specific)
- COVER_IMAGE_API_KEY: API key (uses OPENAI_API_KEY as fallback for OpenAI)
- BANANA_API_KEY: API key for Banana.dev
"""

import os
import logging
import base64
import httpx
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Provider constants
PROVIDER_OPENAI = "openai"
PROVIDER_BANANA = "banana"

# Default models per provider
DEFAULT_MODELS = {
    PROVIDER_OPENAI: "dall-e-3",
    PROVIDER_BANANA: "sdxl",  # or "flux" for newer models
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
    elif provider == PROVIDER_BANANA:
        return _generate_banana_cover(title, author, genre, vibe, aspect_ratio)
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


def _generate_banana_cover(
    title: str,
    author: Optional[str],
    genre: Optional[str],
    vibe: Optional[str],
    aspect_ratio: str
) -> Dict[str, Any]:
    """
    Generate cover image using Banana.dev API.

    Banana.dev provides serverless GPU inference for models like SDXL and Flux.
    This is a cost-effective alternative to DALL-E for high-volume generation.

    Args:
        title: Book title
        author: Author name
        genre: Book genre
        vibe: Visual vibe
        aspect_ratio: Image aspect ratio

    Returns:
        Cover generation result

    Raises:
        ValueError: If API key not configured
        RuntimeError: If API call fails
    """
    api_key = os.getenv("BANANA_API_KEY")
    if not api_key:
        raise ValueError(
            "BANANA_API_KEY not configured. "
            "Set COVER_IMAGE_PROVIDER=openai to use OpenAI DALL-E instead."
        )

    model = os.getenv("COVER_IMAGE_MODEL", DEFAULT_MODELS[PROVIDER_BANANA])
    prompt = _build_cover_prompt(title, author, genre, vibe)

    # Map aspect ratio to dimensions
    size_map = {
        "1:1": (1024, 1024),
        "16:9": (1344, 768),
        "9:16": (768, 1344),
    }
    width, height = size_map.get(aspect_ratio, (1024, 1024))

    logger.info(f"Using Banana.dev model: {model}")
    logger.debug(f"Cover prompt: {prompt}")

    # Banana.dev API endpoint
    # Note: The exact endpoint depends on your deployed model
    # This uses the standard SDXL inference endpoint
    banana_url = "https://api.banana.dev/start/v4/"

    # Model-specific payload
    if model == "flux":
        # Flux model payload
        payload = {
            "prompt": prompt,
            "negative_prompt": "text, watermark, signature, blurry, low quality, distorted",
            "width": width,
            "height": height,
            "num_inference_steps": 30,
            "guidance_scale": 7.5,
        }
        model_key = os.getenv("BANANA_FLUX_MODEL_KEY", "flux-1-schnell")
    else:
        # SDXL model payload
        payload = {
            "prompt": prompt,
            "negative_prompt": "text, watermark, signature, blurry, low quality, distorted, deformed",
            "width": width,
            "height": height,
            "num_inference_steps": 40,
            "guidance_scale": 7.5,
            "scheduler": "DPMSolverMultistepScheduler",
        }
        model_key = os.getenv("BANANA_SDXL_MODEL_KEY", "sdxl")

    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                banana_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "modelKey": model_key,
                    "modelInputs": payload,
                }
            )

            if response.status_code != 200:
                logger.error(f"Banana.dev API error: {response.status_code} - {response.text}")
                raise RuntimeError(f"Banana.dev API error: {response.text}")

            result = response.json()

            # Extract image from response
            # Banana.dev typically returns base64 encoded image
            if "modelOutputs" in result and result["modelOutputs"]:
                output = result["modelOutputs"][0]
                if "image_base64" in output:
                    image_b64 = output["image_base64"]
                elif "image" in output:
                    image_b64 = output["image"]
                else:
                    raise RuntimeError("No image in Banana.dev response")

                image_bytes = base64.b64decode(image_b64)

                return {
                    "provider": PROVIDER_BANANA,
                    "model": model,
                    "image_bytes": image_bytes,
                    "width": width,
                    "height": height,
                    "prompt_used": prompt,
                    "format": "png",
                }
            else:
                raise RuntimeError("Unexpected Banana.dev response format")

    except httpx.TimeoutException:
        logger.error("Banana.dev API timeout")
        raise RuntimeError("Banana.dev API timeout - image generation took too long")
    except Exception as e:
        logger.error(f"Banana.dev cover generation failed: {e}")
        raise


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
