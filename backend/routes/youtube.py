import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_threadpool
from youtube_transcript_api import YouTubeTranscriptApi
from typing import List

from security import get_current_user
from utils import extract_video_id

logger = logging.getLogger(__name__)
router = APIRouter(tags=["youtube"])
youtube_transcript_api = YouTubeTranscriptApi()


@router.get("/youtube-transcript")
async def get_youtube_transcript(
    url: str, 
    languages: List[str] = ["fr", "ja", "zh-TW", "zh-CN", "ko", "en"],
    api_key: str = Depends(get_current_user)
):
    """Fetch transcript from a YouTube video."""
    video_id = extract_video_id(url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL or Video ID")

    try:
        # Run in threadpool as it's a blocking network call
        transcript_list = await run_in_threadpool(
            youtube_transcript_api.fetch, 
            video_id=video_id, 
            languages=languages
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
            "language": languages[0]
        })

    except Exception as e:
        logger.error(f"Error fetching YouTube transcript: {e}")
        raise HTTPException(
            status_code=404, 
            detail=f"Could not fetch transcript for video {video_id}. It might not have captions enabled for the requested languages."
        )
