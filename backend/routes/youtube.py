import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_threadpool
from youtube_transcript_api import YouTubeTranscriptApi
from typing import List, Optional

from core.security import get_current_user
from db import User
from core.utils import extract_video_id, validate_video_id

logger = logging.getLogger(__name__)
router = APIRouter(tags=["youtube"])

FALLBACK_LANGUAGES = ["en", "fr", "ja", "zh-TW", "zh-CN", "ko", "es", "de", "it", "pt", "ru", "ar"]

# Lazy initialization with error handling
_youtube_transcript_api: Optional[YouTubeTranscriptApi] = None

def get_youtube_transcript_api() -> YouTubeTranscriptApi:
    """Get or initialize the YouTube transcript API client."""
    global _youtube_transcript_api
    if _youtube_transcript_api is None:
        try:
            _youtube_transcript_api = YouTubeTranscriptApi()
            logger.info("YouTube transcript API initialized")
        except Exception as e:
            logger.error(f"Failed to initialize YouTube transcript API: {e}")
            raise RuntimeError(f"YouTube transcript service unavailable: {e}")
    return _youtube_transcript_api


@router.get("/youtube-transcript")
async def get_youtube_transcript(
    url: str,
    languages: Optional[List[str]] = Query(default=None),
    current_user: User = Depends(get_current_user)
):
    """Fetch transcript from a YouTube video, preferring the requested language."""
    video_id = extract_video_id(url)
    if not video_id or not validate_video_id(video_id):
        raise HTTPException(status_code=400, detail="Invalid YouTube URL or Video ID")

    # Build language priority list: preferred first, then common fallbacks
    if languages:
        lang_priority = list(languages) + [l for l in FALLBACK_LANGUAGES if l not in languages]
    else:
        lang_priority = FALLBACK_LANGUAGES

    try:
        yt_api = get_youtube_transcript_api()
        # Run in threadpool as it's a blocking network call
        transcript_list = await run_in_threadpool(
            yt_api.fetch,
            video_id=video_id,
            languages=lang_priority
        )

        all_segments = []
        all_text_parts = []

        for i, entry in enumerate(transcript_list):
            start = entry.start
            duration = entry.duration
            text = entry.text.replace('\n', ' ').strip()

            all_segments.append({
                "id": i,
                "start": round(start, 2),
                "end": round(start + duration, 2),
                "text": text
            })
            all_text_parts.append(text)

        full_text = " ".join(all_text_parts)

        return JSONResponse(content={
            "video_id": video_id,
            "text": full_text,
            "segments": all_segments,
            "language": transcript_list.language_code
        })

    except Exception as e:
        logger.error(f"Error fetching YouTube transcript: {e}")
        raise HTTPException(
            status_code=404,
            detail=f"Could not fetch transcript for video {video_id}. It might not have captions enabled."
        )
