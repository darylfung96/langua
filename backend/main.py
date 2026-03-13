"""
Language Learner API Server

Main application entry point. Initializes FastAPI app and registers all routes.
"""
import logging
import json
import os
import sys
import uuid
import uvicorn
from datetime import datetime, timezone
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pathlib import Path
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy.orm import Session

from config import CORS_ORIGINS, IS_PRODUCTION, LOG_LEVEL, LOG_FORMAT
from database import User, get_db, SessionLocal
from file_storage import UPLOADS_DIR, get_media_file_path
from limiter import limiter
from security import decode_token, AUTH_COOKIE_NAME, get_current_user
from csrf import CSRFMiddleware, issue_csrf_token
from routes.auth import router as auth_router
from routes.stories import router as stories_router
from routes.lyrics import router as lyrics_router
from routes.resources import router as resources_router
from routes.transcribe import router as transcribe_router
from routes.youtube import router as youtube_router
from routes.image import router as image_router
from routes.visual import router as visual_router
from routes.story_gen import router as story_gen_router

logger = logging.getLogger(__name__)


def setup_logging():
    """Configure structured logging for the application."""
    log_level = getattr(logging, LOG_LEVEL.upper() if LOG_LEVEL else "INFO")
    log_format = LOG_FORMAT or "development"

    root_logger = logging.getLogger()

    # Remove our own previously added handlers, but keep any from other libraries
    handlers_to_remove = []
    for h in root_logger.handlers:
        if isinstance(h, logging.StreamHandler):
            # Check if it's our handler by looking for our formatter pattern
            if hasattr(h, 'formatter') and h.formatter:
                fmt = getattr(h.formatter, '_fmt', '')
                if fmt and ('Language Learner' in fmt or '%(name)s' in fmt):
                    handlers_to_remove.append(h)
    for h in handlers_to_remove:
        root_logger.removeHandler(h)

    handler = logging.StreamHandler(sys.stdout)

    if log_format == "json":
        class JsonFormatter(logging.Formatter):
            def format(self, record):
                log_obj = {
                    "timestamp": self.formatTime(record, self.datefmt),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                    "module": record.module,
                    "function": record.funcName,
                    "line": record.lineno,
                }
                if hasattr(record, "request_id"):
                    log_obj["request_id"] = record.request_id
                if record.exc_info:
                    log_obj["exc_info"] = self.formatException(record.exc_info)
                return json.dumps(log_obj)

        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="H:M:S"
        ))

    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

setup_logging()


# Improved CORS check
_LOCALHOST_ORIGINS = {"http://localhost:5173", "http://127.0.0.1:5173"}
if CORS_ORIGINS and all(origin in _LOCALHOST_ORIGINS for origin in CORS_ORIGINS):
    logger.warning(
        "CORS_ORIGINS is set to localhost only. "
        "Set the CORS_ORIGINS environment variable to your production domain(s) before deploying."
    )
elif IS_PRODUCTION and any('localhost' in origin or '127.0.0.1' in origin for origin in CORS_ORIGINS):
    logger.warning(
        "Running in production but CORS_ORIGINS contains localhost. "
        "This may prevent legitimate users from accessing your app."
    )


# Create FastAPI app
app = FastAPI(
    title="Language Learner API",
    description="API for language learning with story generation, transcription, and image generation"
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add a unique request ID to each request for tracing."""
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id

    # Inject request_id into log records for this request
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.request_id = request_id
        return record

    logging.setLogRecordFactory(record_factory)

    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        logging.setLogRecordFactory(old_factory)


# Middleware: populate request.state.user_id from JWT for rate limiting
@app.middleware("http")
async def populate_user_id(request: Request, call_next):
    """Extract user ID from JWT token early (before rate limiting)."""
    token = request.cookies.get(AUTH_COOKIE_NAME)
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if token:
        user_id = decode_token(token)
        if user_id:
            request.state.user_id = user_id
    return await call_next(request)


# Attach rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key", "Authorization", "X-CSRF-Token"],
)

# Add CSRF protection middleware
app.add_middleware(CSRFMiddleware)


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


@app.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe - checks if the app is running."""
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/health/ready")
async def readiness_check():
    """Kubernetes readiness probe - checks if dependencies are available."""
    try:
        # Check database connectivity
        db = SessionLocal()
        db.execute("SELECT 1").scalar()
        db.close()

        return {
            "status": "ready",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {
                "database": "connected"
            }
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Dependency unavailable: {str(e)}"
        )


if __name__ == "__main__":
    host = os.getenv("API_HOST", "127.0.0.1")
    uvicorn.run("main:app", host=host, port=8000, workers=1, reload=False)





  