"""Shared Gemini client singleton with lazy initialization.

Both the image-generation and story-generation routes import from here so
only one GeminiClient is created for the entire process.
"""
import json
import logging
import re
from typing import Optional
import asyncio

from gemini_webapi import GeminiClient

from config import GEMINI_COOKIE_1PSID, GEMINI_COOKIE_1PSIDTS, AI_REQUEST_TIMEOUT, IS_PRODUCTION
from constants import LANGUAGE_NAMES

logger = logging.getLogger(__name__)

gemini_client: Optional[GeminiClient] = None
_client_lock = asyncio.Lock()
_client_initialized = False


async def generate_shadowing_phrases(theme: str, language: str, num_phrases: int = 5):
    """Generate phrases suitable for shadowing practice using Gemini AI."""
    client = await get_gemini_client()

    language_display = LANGUAGE_NAMES.get(language, language)

    prompt = (
        f"Generate {num_phrases} natural, conversational phrases in {language_display} "
        f"about the theme: \"{theme}\".\n\n"
        "Requirements:\n"
        "1. Phrases should be 5-10 words each, suitable for shadowing practice\n"
        "2. Include common pronunciation challenges (contractions, liaison, etc.)\n"
        "3. Provide English translations\n"
        "4. Provide word-level breakdown with approximate pronunciation difficulty (optional)\n\n"
        "Return ONLY valid JSON with this exact structure (no markdown):\n"
        "{\n"
        '  "phrases": [\n'
        "    {\n"
        '      "text": "Original phrase in {language_display}",\n'
        '      "translation": "English translation",\n'
        '      "words": [\n'
        '        {"text": "word1", "difficulty": "easy|medium|hard"}\n'
        "      ]\n"
        "    }\n"
        "  ]\n"
        "}"
    )

    response = await asyncio.wait_for(
        client.generate_content(prompt), timeout=AI_REQUEST_TIMEOUT
    )

    if not response.text:
        raise ValueError("No response from Gemini")

    # Sanitize JSON
    text = response.text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    text = text.rstrip("`").strip()
    text = re.sub(r'\\(?!["\\/bfnrtu])', '', text)

    data = json.loads(text)

    if "phrases" not in data or not isinstance(data["phrases"], list):
        raise ValueError("Invalid response format")

    return data["phrases"]


async def get_gemini_client() -> GeminiClient:
    """
    Get or initialize the Gemini client singleton with lazy initialization.
    The client is initialized only on first use and reused for subsequent requests.

    Returns:
        Initialized GeminiClient instance

    Raises:
        RuntimeError: If Gemini credentials are not configured or initialization fails
    """
    global gemini_client, _client_initialized

    if gemini_client is None:
        async with _client_lock:
            if not _client_initialized:
                if not GEMINI_COOKIE_1PSID:
                    raise RuntimeError(
                        "Gemini service is not configured. "
                        "Set GEMINI_COOKIE_1PSID environment variable."
                    )
                try:
                    # Configure SSL verification: disabled only in development, enforced in production
                    verify_ssl = not IS_PRODUCTION
                    if not verify_ssl:
                        logger.warning("SSL certificate verification disabled for Gemini (development only)")
                    client = GeminiClient(
                        GEMINI_COOKIE_1PSID,
                        GEMINI_COOKIE_1PSIDTS or "",
                        proxy=None,
                        verify=verify_ssl
                    )
                    # Initialize the client (establishes session)
                    await client.init(
                        timeout=30,
                        auto_close=False,
                        close_delay=300,
                        auto_refresh=True
                    )
                    # Only assign to global after successful initialization
                    gemini_client = client
                    _client_initialized = True
                    logger.info("Gemini client initialized successfully")
                except Exception as e:
                    logger.error(f"Failed to initialize Gemini client: {e}")
                    raise RuntimeError(f"Gemini client initialization failed: {e}")

    return gemini_client
