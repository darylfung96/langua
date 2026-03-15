"""Pydantic models specific to the shadowing feature.

These were previously inline in routes/shadowing.py.
"""
import re
from pydantic import BaseModel, field_validator, Field
from typing import List, Optional

from constants import DANGEROUS_CHARS_PATTERN
from core.sanitization import sanitize_html
from schemas.common import validate_language


class GeneratePhrasesRequest(BaseModel):
    theme: str = Field(min_length=1, max_length=255)
    language: str = Field(min_length=1, max_length=100)
    num_phrases: int = Field(default=5, ge=1, le=20)

    @field_validator("language")
    @classmethod
    def validate_language_code(cls, v: str) -> str:
        return validate_language(v)

    @field_validator("theme")
    @classmethod
    def validate_theme(cls, v: str) -> str:
        if re.search(DANGEROUS_CHARS_PATTERN, v):
            raise ValueError("Theme contains invalid characters")
        sanitized = sanitize_html(v)
        if not sanitized or not sanitized.strip():
            raise ValueError("Theme cannot be empty after sanitization")
        return sanitized.strip()


class StartSessionRequest(BaseModel):
    theme: str = Field(min_length=1, max_length=255)
    language: str = Field(min_length=1, max_length=100)
    phrases: str  # JSON string

    @field_validator("language")
    @classmethod
    def validate_language_code(cls, v: str) -> str:
        return validate_language(v)


class RecordAttemptRequest(BaseModel):
    session_id: str
    phrase_id: int
    phrase_text: str
    transcript: str
    accuracy_score: float = Field(ge=0.0, le=1.0)
    words_matched: int = Field(ge=0)
    total_words: int = Field(ge=0)


class TTSRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    language: str = Field(min_length=1, max_length=100)

    @field_validator("language")
    @classmethod
    def validate_language_code(cls, v: str) -> str:
        return validate_language(v)
