"""Gemini Text-to-Speech (TTS) using the official Google GenAI SDK.

Provides async function generate_tts() that returns audio data and MIME type.
Requires GEMINI_API_KEY for authentication.
"""
import logging
import asyncio
from typing import Optional, Tuple

from config import GEMINI_API_KEY, AI_REQUEST_TIMEOUT
from constants import LANGUAGE_NAMES

logger = logging.getLogger(__name__)


def _get_language_name(language_code: str) -> str:
    """Get display name for a language code."""
    return LANGUAGE_NAMES.get(language_code, language_code)


async def generate_tts(language: str, title: str, story: str) -> Tuple[bytes, str]:
    """
    Generate TTS audio for a story using the official Gemini API.

    Args:
        language: BCP 47 language code (e.g., 'en', 'fr', 'es')
        title: Story title (plain text)
        story: Story content (plain text, without HTML)

    Returns:
        Tuple of (audio_bytes, mime_type)

    Raises:
        RuntimeError: If GEMINI_API_KEY is not configured or initialization fails
        ValueError: If no audio is returned from the API
    """
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "Gemini API key is required for audio generation. "
            "Set GEMINI_API_KEY environment variable with a key from https://aistudio.google.com/app/apikey"
        )

    try:
        # Import google-genai only when needed to avoid unnecessary dependency if not used
        from google import genai
        from google.genai import types
    except ImportError as e:
        logger.error("Failed to import google-genai. Make sure it's installed: pip install google-genai")
        raise RuntimeError("Google GenAI SDK is not installed.") from e

    # Initialize client
    client = genai.Client(api_key=GEMINI_API_KEY)

    # Build prompt
    language_name = _get_language_name(language)
    prompt = (
        f"Please read the following story aloud in {language_name}:\n\n"
        f"{title}\n\n{story}"
    )

    # Use the specialized TTS preview model with the 'Kore' voice.
    model = "gemini-2.5-flash-preview-tts"

    # Configure for audio output
    generate_content_config = types.GenerateContentConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Leda")
            )
        ),
    )

    try:
        # Run the blocking call in a thread pool to avoid blocking the event loop
        loop = asyncio.get_running_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=generate_content_config,
                )
            ),
            timeout=AI_REQUEST_TIMEOUT,
        )

        # Extract audio from response
        # The response structure: response.candidates[0].content.parts[0].inline_data
        if not response.candidates:
            raise ValueError("No candidates in response")

        candidate = response.candidates[0]
        if not candidate.content or not candidate.content.parts:
            raise ValueError("No content parts in response")

        for part in candidate.content.parts:
            if part.inline_data and part.inline_data.mime_type and part.inline_data.mime_type.startswith("audio/"):
                audio_bytes = part.inline_data.data
                mime_type = part.inline_data.mime_type
                logger.info(f"Generated audio: mime_type={mime_type}, size={len(audio_bytes)} bytes")
                return audio_bytes, mime_type

        raise ValueError("No audio data found in response")

    except asyncio.TimeoutError:
        logger.error(f"Gemini TTS request timed out after {AI_REQUEST_TIMEOUT} seconds")
        raise
    except Exception as e:
        logger.error(f"Error generating TTS with Gemini: {e}", exc_info=True)
        raise
