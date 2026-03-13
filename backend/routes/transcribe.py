import os
import uuid
import shutil
import asyncio
import logging
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_threadpool
from faster_whisper import WhisperModel
import torch

from config import WHISPER_MODEL_NAME, WHISPER_MAX_UPLOAD_SIZE, TEMP_DIR
from security import get_current_user
from limiter import limiter

logger = logging.getLogger(__name__)
router = APIRouter(tags=["transcription"])

# Initialize faster-whisper model
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
COMPUTE_TYPE = "float16" if torch.cuda.is_available() else "int8"

try:
    model = WhisperModel(WHISPER_MODEL_NAME, device=DEVICE, compute_type=COMPUTE_TYPE)
except Exception as e:
    logger.error(f"Error initializing faster-whisper: {e}")
    model = None

SUPPORTED_FORMATS = (".wav", ".mp3", ".m4a", ".ogg", ".flac", ".mp4", ".mkv", ".avi", ".mov", ".webm")


@router.post("/transcribe")
@limiter.limit("10/minute")
async def transcribe(
    request: Request,
    file: UploadFile = File(...),
    language: str = None,
    api_key: str = Depends(get_current_user)
):
    """Transcribe audio/video file using Whisper."""
    if file.size and file.size > WHISPER_MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 50MB.")

    if model is None:
        raise HTTPException(status_code=500, detail="Whisper model not initialized")

    if not file.filename.lower().endswith(SUPPORTED_FORMATS):
        raise HTTPException(status_code=400, detail=f"Unsupported file format. Supported: {', '.join(SUPPORTED_FORMATS)}")

    tmp_file = tempfile.NamedTemporaryFile(
        dir=TEMP_DIR,
        suffix=os.path.splitext(file.filename)[1] or ".tmp",
        delete=False,
    )
    temp_path = tmp_file.name
    tmp_file.close()

    try:
        async with asyncio.Lock():
            with open(temp_path, "wb") as buffer:
                await run_in_threadpool(shutil.copyfileobj, file.file, buffer)

        segments, info = await run_in_threadpool(
            model.transcribe,
            temp_path,
            beam_size=5,
            language=language if language else None,
            word_timestamps=True
        )

        all_segments = []
        all_text_parts = []

        for segment in segments:
            all_segments.append({
                "id": len(all_segments),
                "start": round(segment.start, 2),
                "end": round(segment.end, 2),
                "text": segment.text.strip()
            })
            all_text_parts.append(segment.text.strip())

        full_text = " ".join(all_text_parts)

        return JSONResponse(content={
            "filename": file.filename,
            "text": full_text,
            "segments": all_segments,
            "language": info.language,
            "language_probability": info.language_probability
        })

    except Exception as e:
        logger.error(f"Error during transcription: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal server error occurred.")
    finally:
        if os.path.exists(temp_path):
            await run_in_threadpool(os.remove, temp_path)
