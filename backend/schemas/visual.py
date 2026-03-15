import json
import re
from pydantic import BaseModel, field_validator, Field
from typing import Any, Optional

from constants import (
    MAX_LANGUAGE_LENGTH,
    MAX_WORD_LENGTH,
    MAX_PROMPT_LENGTH,
    MAX_EXPLANATION_LENGTH,
    DANGEROUS_CHARS_PATTERN,
)
from core.sanitization import sanitize_html
from schemas.common import validate_language


class VisualRequest(BaseModel):
    word: str = Field(min_length=1, max_length=MAX_WORD_LENGTH)
    language: str = Field(min_length=1, max_length=MAX_LANGUAGE_LENGTH)
    images: str = Field(min_length=2)  # at least "[]"
    prompt: str = Field(min_length=1, max_length=MAX_PROMPT_LENGTH)
    explanation: Optional[str] = Field(default=None, max_length=MAX_EXPLANATION_LENGTH)

    @field_validator("language")
    @classmethod
    def validate_language_code(cls, v: str) -> str:
        return validate_language(v)

    @field_validator("word")
    @classmethod
    def validate_word(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Word cannot be empty")
        if len(v) > 100:
            raise ValueError("Word is too long (max 100 characters)")
        if re.search(DANGEROUS_CHARS_PATTERN, v):
            raise ValueError("Word contains invalid characters")
        return v.strip()


class VisualDetailResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    word: str
    language: str
    images: Any
    prompt: str
    explanation: Optional[str] = None
    created_at: str
    updated_at: str

    @field_validator("images", mode="before")
    @classmethod
    def parse_images(cls, v: Any) -> Any:
        return json.loads(v) if isinstance(v, str) else v

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def datetime_to_str(cls, v: Any) -> str:
        return v.isoformat() if hasattr(v, "isoformat") else v


class SavedVisualListItem(BaseModel):
    id: str
    word: str
    language: str
    created_at: str
    updated_at: str


# Legacy alias
VisualResponse = VisualDetailResponse
