"""Shared Gemini client singleton.

Both the image-generation and story-generation routes import from here so
only one GeminiClient is created for the entire process.
"""
import logging
from typing import Optional

from gemini_webapi import GeminiClient

from config import GEMINI_COOKIE_1PSID, GEMINI_COOKIE_1PSIDTS

logger = logging.getLogger(__name__)

gemini_client: Optional[GeminiClient] = None

if GEMINI_COOKIE_1PSID:
    try:
        gemini_client = GeminiClient(GEMINI_COOKIE_1PSID, GEMINI_COOKIE_1PSIDTS, proxy=None)
        logger.info("Gemini client created (will be initialized on first use)")
    except Exception as e:
        logger.warning(f"Failed to create Gemini client: {e}")
