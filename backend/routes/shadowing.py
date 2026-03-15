"""Shadowing practice endpoints.

Handles phrase generation, session management, attempt recording, and TTS.
"""
import asyncio
import json
import logging
import re
from typing import List

from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from config import AI_REQUEST_TIMEOUT
from core.security import get_current_user
from db import User, get_db, ShadowingSession, ShadowingAttempt
from clients.gemini import get_gemini_client
from clients.tts import generate_tts_audio
from core.limiter import limiter
from slowapi.util import get_remote_address
from constants import LANGUAGE_NAMES, LANGUAGE_PATTERN, DANGEROUS_CHARS_PATTERN
from core.sanitization import sanitize_html

logger = logging.getLogger(__name__)
router = APIRouter(tags=["shadowing"])


def _sanitize_json_text(text: str) -> str:
    """Strip markdown fences and fix invalid JSON escape sequences from AI responses."""
    if not text:
        raise ValueError("Empty AI response")
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    text = text.rstrip("`").strip()
    # Remove backslashes before characters that are not valid JSON escape characters.
    text = re.sub(r'\\(?!["\\/bfnrtu])', '', text)
    return text


# HTML sanitization imported from centralized module
# (removed local wrapper that imported from schemas)


# Language validation pattern (BCP 47 basic)
_language_regex = re.compile(LANGUAGE_PATTERN)


def _validate_language(v: str) -> str:
    """Validate language code format."""
    if not v:
        raise ValueError("Language is required")
    if not _language_regex.match(v):
        raise ValueError(f"Invalid language format: {v}. Use format like 'en', 'en-US', 'zh-CN'")
    return v


class GeneratePhrasesRequest(BaseModel):
    theme: str = Field(min_length=1, max_length=255)
    language: str = Field(min_length=1, max_length=100)
    num_phrases: int = Field(default=5, ge=1, le=20)

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        return _validate_language(v)

    @field_validator("theme")
    @classmethod
    def validate_theme(cls, v: str) -> str:
        # Check for dangerous characters first
        if re.search(DANGEROUS_CHARS_PATTERN, v):
            raise ValueError("Theme contains invalid characters")
        # Sanitize HTML
        sanitized = sanitize_html(v)
        if not sanitized or not sanitized.strip():
            raise ValueError("Theme cannot be empty after sanitization")
        return sanitized.strip()


class StartSessionRequest(BaseModel):
    theme: str = Field(min_length=1, max_length=255)
    language: str = Field(min_length=1, max_length=100)

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        return _validate_language(v)

    @field_validator("theme")
    @classmethod
    def validate_theme(cls, v: str) -> str:
        # Check for dangerous characters first
        if re.search(DANGEROUS_CHARS_PATTERN, v):
            raise ValueError("Theme contains invalid characters")
        # Sanitize HTML
        sanitized = sanitize_html(v)
        if not sanitized or not sanitized.strip():
            raise ValueError("Theme cannot be empty after sanitization")
        return sanitized.strip()


class RecordAttemptRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=100)
    phrase_index: int = Field(ge=0, le=1000)  # Reasonable upper bound
    phrase_text: str = Field(min_length=1)
    accuracy_score: float = Field(ge=0, le=100)
    words_matched: int = Field(ge=0)
    total_words: int = Field(gt=0)


@router.post("/generate")
@limiter.limit("10/minute", key_func=get_remote_address)
async def generate_phrases(
    request: Request,
    body: GeneratePhrasesRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate shadowing phrases using Gemini."""
    try:
        client = await get_gemini_client()

        language_display = LANGUAGE_NAMES.get(body.language, body.language)

        prompt = (
            f"Generate {body.num_phrases} natural, conversational phrases in {language_display} "
            f"about the theme: \"{body.theme}\".\n\n"
            "Requirements:\n"
            "1. Phrases should be 5-10 words each, suitable for shadowing practice\n"
            "2. Include common pronunciation challenges (contractions, liaison, etc.)\n"
            "3. Provide English translations\n"
            "4. Provide word-level breakdown with approximate pronunciation difficulty (optional)\n\n"
            "Return ONLY valid JSON with this exact structure (no markdown):\n"
            "{\n"
            '  "phrases": [\n'
            "    {\n"
            '      "text": "Original phrase in {language_display}",\n'
            '      "translation": "English translation",\n'
            '      "words": [\n'
            '        {"text": "word1", "difficulty": "easy|medium|hard"}\n'
            "      ]\n"
            "    }\n"
            "  ]\n"
            "}"
        )

        response = await asyncio.wait_for(
            client.generate_content(prompt), timeout=AI_REQUEST_TIMEOUT
        )

        if not response.text:
            raise HTTPException(status_code=500, detail="No phrases generated.")

        phrases_data = json.loads(_sanitize_json_text(response.text))

        # Validate structure
        if "phrases" not in phrases_data or not isinstance(phrases_data["phrases"], list):
            raise HTTPException(status_code=500, detail="Invalid response format from AI.")

        return JSONResponse(content={"phrases": phrases_data["phrases"]})

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini phrases response as JSON: {e}")
        raise HTTPException(status_code=500, detail="AI returned an invalid response format.")
    except asyncio.TimeoutError:
        logger.error("Gemini phrase generation timed out")
        raise HTTPException(status_code=504, detail="AI request timed out. Please try again.")
    except HTTPException:
        raise
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating phrases: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate phrases.")


@router.post("/start-session")
@limiter.limit("30/minute", key_func=get_remote_address)
async def start_session(
    request: Request,
    body: StartSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new shadowing session."""
    session = ShadowingSession(
        user_id=current_user.id,
        theme=body.theme,
        language=body.language
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return {"session_id": session.id}


@router.post("/record-attempt")
@limiter.limit("60/minute", key_func=get_remote_address)
async def record_attempt(
    request: Request,
    body: RecordAttemptRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record a shadowing attempt."""
    # Verify session belongs to user
    session = db.query(ShadowingSession).filter(
        ShadowingSession.id == body.session_id,
        ShadowingSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    attempt = ShadowingAttempt(
        session_id=body.session_id,
        phrase_id=body.phrase_index,
        phrase_text=body.phrase_text,
        accuracy_score=body.accuracy_score,
        words_matched=body.words_matched,
        total_words=body.total_words
    )
    db.add(attempt)
    db.commit()

    return {"success": True}


@router.get("/history")
async def get_history(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's shadowing history."""
    sessions = db.query(ShadowingSession).filter(
        ShadowingSession.user_id == current_user.id
    ).order_by(ShadowingSession.created_at.desc()).limit(limit).all()

    result = []
    for session in sessions:
        attempts = db.query(ShadowingAttempt).filter(
            ShadowingAttempt.session_id == session.id
        ).order_by(ShadowingAttempt.phrase_id.asc()).all()

        result.append({
            "session_id": session.id,
            "theme": session.theme,
            "language": session.language,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "attempts": [
                {
                    "phrase_index": a.phrase_id,
                    "phrase_text": a.phrase_text,
                    "accuracy_score": a.accuracy_score,
                    "words_matched": a.words_matched,
                    "total_words": a.total_words,
                    "attempted_at": a.attempted_at.isoformat() if a.attempted_at else None
                }
                for a in attempts
            ]
        })

    return {"history": result}


# ── Text-to-Speech endpoint ────────────────────────────────────────────────

class TTSRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1000)
    language: str = Field(min_length=1, max_length=20)

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        return _validate_language(v)

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Text cannot be empty")
        if re.search(DANGEROUS_CHARS_PATTERN, stripped):
            raise ValueError("Text contains invalid characters")
        return stripped


@router.post("/tts")
@limiter.limit("60/minute", key_func=get_remote_address)
async def text_to_speech(
    request: Request,
    body: TTSRequest,
    current_user: User = Depends(get_current_user),
):
    """Convert text to speech using Google Cloud TTS (WaveNet voices).

    Returns base64-encoded MP3 audio. Caching, retries, and circuit
    breaking are handled by tts_client.
    """
    audio_content = await generate_tts_audio(body.text, body.language)
    return {"audioContent": audio_content}
