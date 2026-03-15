"""core/utils — merged helpers from utils.py and api_utils.py.

Previously two separate files:
- utils.py    (48 LOC) — date/time formatting, YouTube ID parsing, image prompts
- api_utils.py (54 LOC) — standardized FastAPI response helpers

Both are kept here as a single module.  The old files remain as shims.
"""
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import HTTPException
from fastapi.responses import JSONResponse


# ─── Date / string helpers ────────────────────────────────────────────────────

def format_timestamp(dt: Optional[datetime]) -> Optional[str]:
    """Format a datetime as ISO 8601. Returns None if dt is None."""
    return dt.isoformat() if dt is not None else None


def extract_video_id(youtube_url: str) -> str:
    """Extract the video ID from a YouTube URL or return the input if it already is an ID."""
    if len(youtube_url) == 11 and re.match(r"^[0-9A-Za-z_-]{11}$", youtube_url):
        return youtube_url

    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11})(?:[&?\/]|$)",
        r"youtu\.be\/([0-9A-Za-z_-]{11})(?:[&?\/]|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, youtube_url)
        if match:
            return match.group(1)
    return None


def validate_video_id(video_id: str) -> bool:
    """Return True iff video_id is a valid 11-char YouTube video ID."""
    if not video_id:
        return False
    return len(video_id) == 11 and bool(re.fullmatch(r"[0-9A-Za-z_-]{11}", video_id))


def generate_creative_prompt(word: str, language: str) -> str:
    """Build an image-generation prompt that aids word memorisation."""
    return (
        f"Create a vibrant, imaginative, and memorable illustration that captures the "
        f"essence of the {language} word '{word}'.\n\n"
        "The image should be:\n"
        "- Highly visual and vivid with bright, memorable colors\n"
        "- Filled with visual metaphors and symbolic elements that help remember the word\n"
        "- Creative and whimsical, making it unforgettable\n"
        "- Clear and detailed so the word's meaning is instantly obvious\n\n"
        "Style: Modern illustration, vivid colors, detailed, engaging, "
        "perfect for language learning flashcards."
    )


# ─── FastAPI response helpers ─────────────────────────────────────────────────

def success_response(data: Any = None, message: str = "Success") -> JSONResponse:
    """Return a standardized success JSONResponse."""
    return JSONResponse(content={"success": True, "message": message, "data": data})


def error_response(
    status_code: int,
    message: str,
    details: Any = None,
) -> HTTPException:
    """Build a standardized HTTPException with a consistent error payload."""
    content: Dict[str, Any] = {"success": False, "message": message}
    if details:
        content["details"] = details
    return HTTPException(status_code=status_code, detail=content)


def api_success(data: Any = None, message: str = "Success") -> Dict[str, Any]:
    """Build a success dict for use in manual JSONResponse construction."""
    return {"success": True, "message": message, "data": data}


def api_error(message: str, details: Any = None) -> Dict[str, Any]:
    """Build an error dict."""
    error: Dict[str, Any] = {"message": message}
    if details:
        error["details"] = details
    return error
