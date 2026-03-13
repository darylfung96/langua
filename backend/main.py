"""
Language Learner API Server

Main application entry point. Initializes FastAPI app and registers all routes.
"""
import logging
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from config import CORS_ORIGINS
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

# Create FastAPI app
app = FastAPI(
    title="Language Learner API",
    description="API for language learning with story generation, transcription, and image generation"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "X-API-Key"],
)

# Register routers
app.include_router(stories_router, prefix="/stories")
app.include_router(lyrics_router)
app.include_router(resources_router, prefix="/resources")
app.include_router(transcribe_router)
app.include_router(youtube_router)
app.include_router(image_router)
app.include_router(visual_router, prefix="/visuals")
app.include_router(story_gen_router, prefix="/gemini")

# Mount static files for uploads
uploads_dir = Path(__file__).parent / "uploads"
uploads_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    host = os.getenv("API_HOST", "127.0.0.1")
    uvicorn.run("main:app", host=host, port=8000, workers=1, reload=False)
