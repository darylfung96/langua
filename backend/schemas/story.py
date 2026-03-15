import json
from pydantic import BaseModel, field_validator, Field
from typing import Any, Optional

from constants import (
    MAX_TITLE_LENGTH,
    MAX_STORY_CONTENT_LENGTH,
    MAX_LANGUAGE_LENGTH,
    MAX_AUDIO_BASE64_LENGTH,
)
from core.sanitization import sanitize_html
from schemas.common import validate_language


class StoryRequest(BaseModel):
    title: str = Field(min_length=1, max_length=MAX_TITLE_LENGTH)
    story_content: str = Field(min_length=1, max_length=MAX_STORY_CONTENT_LENGTH)
    language: str = Field(min_length=1, max_length=MAX_LANGUAGE_LENGTH)
    vocabulary: str = Field(min_length=2)  # at least "[]"
    quiz: Optional[str] = None
    audio: Optional[str] = Field(default=None, max_length=MAX_AUDIO_BASE64_LENGTH)

    @field_validator("language")
    @classmethod
    def validate_language_code(cls, v: str) -> str:
        return validate_language(v)

    @field_validator("story_content")
    @classmethod
    def sanitize_story_content(cls, v: str) -> str:
        return sanitize_html(v)


class StoryDetailResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    title: str
    story_content: str
    language: str
    vocabulary: Any
    quiz: Optional[Any] = None
    audio_file_path: Optional[str] = None
    created_at: str
    updated_at: str

    @field_validator("vocabulary", mode="before")
    @classmethod
    def parse_vocabulary(cls, v: Any) -> Any:
        return json.loads(v) if isinstance(v, str) else v

    @field_validator("quiz", mode="before")
    @classmethod
    def parse_quiz(cls, v: Any) -> Any:
        if v is None:
            return None
        return json.loads(v) if isinstance(v, str) else v

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def datetime_to_str(cls, v: Any) -> str:
        return v.isoformat() if hasattr(v, "isoformat") else v


class SavedStoryListItem(BaseModel):
    id: str
    title: str
    language: str
    created_at: str
    updated_at: str


# Legacy alias
StoryResponse = StoryDetailResponse
