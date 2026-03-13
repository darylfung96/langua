"""Shared Gemini client singleton with lazy initialization.

Both the image-generation and story-generation routes import from here so
only one GeminiClient is created for the entire process.
"""
import logging
from typing import Optional
import asyncio

from gemini_webapi import GeminiClient

from config import GEMINI_COOKIE_1PSID, GEMINI_COOKIE_1PSIDTS, AI_REQUEST_TIMEOUT

logger = logging.getLogger(__name__)

gemini_client: Optional[GeminiClient] = None
_client_lock = asyncio.Lock()
_client_initialized = False


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
                    gemini_client = GeminiClient(
                        GEMINI_COOKIE_1PSID,
                        GEMINI_COOKIE_1PSIDTS or "",
                        proxy=None
                    )
                    # Initialize the client ( establishes session)
                    await gemini_client.init(timeout=30, auto_close=False, close_delay=300, auto_refresh=True)
                    _client_initialized = True
                    logger.info("Gemini client initialized successfully")
                except Exception as e:
                    logger.error(f"Failed to initialize Gemini client: {e}")
                    raise RuntimeError(f"Gemini client initialization failed: {e}")

    return gemini_client
