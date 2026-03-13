"""
Language Learner API Server

Main application entry point. Initializes FastAPI app and registers all routes.
"""
import logging
import os
import uvicorn
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pathlib import Path
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from config import CORS_ORIGINS
from database import User
from file_storage import UPLOADS_DIR, get_media_file_path
from limiter import limiter
from security import get_current_user
from routes.auth import router as auth_router
from routes.stories import router as stories_router
from routes.lyrics import router as lyrics_router
from routes.resources import router as resources_router
from routes.transcribe import router as transcribe_router
from routes.youtube import router as youtube_router
from routes.image import router as image_router
from routes.visual import router as visual_router
from routes.story_gen import router as story_gen_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_LOCALHOST_ORIGINS = {"http://localhost:5173", "http://127.0.0.1:5173"}
if all(o in _LOCALHOST_ORIGINS for o in CORS_ORIGINS):
    logger.warning(
        "CORS_ORIGINS is set to localhost only. "
        "Set the CORS_ORIGINS environment variable to your production domain(s) before deploying."
    )

# Rate limiter — default: 60 requests/minute per IP (defined in limiter.py)

# Create FastAPI app
app = FastAPI(
    title="Language Learner API",
    description="API for language learning with story generation, transcription, and image generation"
)

# Attach rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "X-API-Key", "Authorization"],
)

# Register routers
app.include_router(auth_router)
app.include_router(stories_router, prefix="/stories")
app.include_router(lyrics_router)
app.include_router(resources_router, prefix="/resources")
app.include_router(transcribe_router)
app.include_router(youtube_router)
app.include_router(image_router)
app.include_router(visual_router, prefix="/visuals")
app.include_router(story_gen_router, prefix="/gemini")

@app.get("/uploads/{filename}")
async def serve_upload(
    filename: str,
    current_user: User = Depends(get_current_user),
):
    """Serve an uploaded media file. Requires a valid JWT."""
    try:
        file_path = get_media_file_path(f"uploads/{filename}")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file path")
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    host = os.getenv("API_HOST", "127.0.0.1")
    uvicorn.run("main:app", host=host, port=8000, workers=1, reload=False)

