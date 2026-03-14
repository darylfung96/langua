import re
from datetime import datetime, timezone
from typing import Optional


def format_timestamp(dt: Optional[datetime]) -> Optional[str]:
    """Format a datetime as ISO 8601. Returns None if dt is None."""
    return dt.isoformat() if dt is not None else None


def extract_video_id(youtube_url: str) -> str:
    """Extracts the video ID from a YouTube URL or returns the input if it looks like an ID."""
    if len(youtube_url) == 11 and re.match(r"^[0-9A-Za-z_-]{11}$", youtube_url):
        return youtube_url

    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11})(?:[&?\/]|$)",  # watch?v=ID, /v/ID, /embed/ID
        r"youtu\.be\/([0-9A-Za-z_-]{11})(?:[&?\/]|$)"  # youtu.be/ID
    ]

    for pattern in patterns:
        match = re.search(pattern, youtube_url)
        if match:
            return match.group(1)

    return None


def validate_video_id(video_id: str) -> bool:
    """Validate that a YouTube video ID is properly formatted."""
    if not video_id:
        return False
    return len(video_id) == 11 and bool(re.fullmatch(r"[0-9A-Za-z_-]{11}", video_id))


def generate_creative_prompt(word: str, language: str) -> str:
    """Generate a creative, memorable prompt for image generation based on the word and language."""
    prompt = f"""Create a vibrant, imaginative, and memorable illustration that captures the essence of the {language} word '{word}'.
    
The image should be:
- Highly visual and vivid with bright, memorable colors
- Filled with visual metaphors and symbolic elements that help remember the word
- Creative and whimsical, making it unforgettable
- Clear and detailed so the word's meaning is instantly obvious

Style: Modern illustration, vivid colors, detailed, engaging, perfect for language learning flashcards."""
    
    return prompt
