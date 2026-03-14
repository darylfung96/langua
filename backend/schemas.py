import json
import re
import logging
from pydantic import BaseModel, field_validator, EmailStr, Field, model_validator
from typing import Any, List, Optional

# Use shared constants
from constants import (
    MAX_TITLE_LENGTH,
    MAX_STORY_CONTENT_LENGTH,
    MAX_LANGUAGE_LENGTH,
    MAX_WORD_LENGTH,
    MAX_PROMPT_LENGTH,
    MAX_EXPLANATION_LENGTH,
    MAX_AUDIO_BASE64_LENGTH,
    MAX_VIDEO_ID_LENGTH,
    MAX_FILE_NAME_LENGTH,
    MAX_FILE_TYPE_LENGTH,
    LANGUAGE_PATTERN,
    DANGEROUS_CHARS_PATTERN,
)

# Import centralized HTML sanitization
from sanitization import sanitize_html

# Language code validation regex
_language_regex = re.compile(LANGUAGE_PATTERN)

def _validate_language(v: str) -> str:
    """Validate language code format (BCP 47 basic)."""
    if not v:
        raise ValueError("Language is required")
    if not _language_regex.match(v):
        raise ValueError(f"Invalid language format: {v}. Use format like 'en', 'en-US', 'zh-CN'")
    return v


class VocabWord(BaseModel):
    word: str
    meaning_in_target: str
    equivalent_in_english: str


# ---------------------------------------------------------------------------
# Auth schemas
# ---------------------------------------------------------------------------

class UserRegister(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    csrf_token: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    email: str
    created_at: str

    model_config = {"from_attributes": True}

    @field_validator("created_at", mode="before")
    @classmethod
    def datetime_to_str(cls, v: Any) -> str:
        return v.isoformat() if hasattr(v, "isoformat") else v


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class StoryRequest(BaseModel):
    title: str = Field(min_length=1, max_length=MAX_TITLE_LENGTH)
    story_content: str = Field(min_length=1, max_length=MAX_STORY_CONTENT_LENGTH)
    language: str = Field(min_length=1, max_length=MAX_LANGUAGE_LENGTH)
    vocabulary: str = Field(min_length=2)  # at least "[]"
    quiz: Optional[str] = None
    audio: Optional[str] = Field(default=None, max_length=MAX_AUDIO_BASE64_LENGTH)

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        return _validate_language(v)

    @field_validator("story_content")
    @classmethod
    def sanitize_story_content(cls, v: str) -> str:
        """Sanitize HTML to prevent XSS if content is rendered in frontend."""
        return sanitize_html(v)


class LyricRequest(BaseModel):
    title: str = Field(min_length=1, max_length=MAX_TITLE_LENGTH)
    video_id: str = Field(min_length=1, max_length=MAX_VIDEO_ID_LENGTH)
    language: str = Field(min_length=1, max_length=MAX_LANGUAGE_LENGTH)
    transcript: str = Field(min_length=2)  # at least "[]"

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        return _validate_language(v)

    @field_validator("video_id")
    @classmethod
    def validate_video_id_format(cls, v: str) -> str:
        from utils import validate_video_id
        if not validate_video_id(v):
            raise ValueError("Invalid YouTube video ID format")
        return v


class ResourceRequest(BaseModel):
    title: str = Field(min_length=1, max_length=MAX_TITLE_LENGTH)
    file_name: str = Field(min_length=1, max_length=MAX_FILE_NAME_LENGTH)
    file_type: str = Field(min_length=1, max_length=MAX_FILE_TYPE_LENGTH)
    language: str = Field(min_length=1, max_length=MAX_LANGUAGE_LENGTH)
    transcript: str = Field(min_length=2)  # at least "[]"
    media_file_path: Optional[str] = None

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        return _validate_language(v)

    @field_validator("file_name")
    @classmethod
    def validate_file_name(cls, v: str) -> str:
        # Prevent path traversal and ensure safe filename
        if '..' in v or '/' in v or '\\' in v:
            raise ValueError("Invalid file name")
        return v


class VisualRequest(BaseModel):
    word: str = Field(min_length=1, max_length=MAX_WORD_LENGTH)
    language: str = Field(min_length=1, max_length=MAX_LANGUAGE_LENGTH)
    images: str = Field(min_length=2)  # at least "[]"
    prompt: str = Field(min_length=1, max_length=MAX_PROMPT_LENGTH)
    explanation: Optional[str] = Field(default=None, max_length=MAX_EXPLANATION_LENGTH)

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        return _validate_language(v)

    @field_validator("word")
    @classmethod
    def validate_word(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Word cannot be empty")
        # Limit word length (already via Field, but add content check)
        if len(v) > 100:
            raise ValueError("Word is too long (max 100 characters)")
        # Check for dangerous characters before sanitization
        if re.search(DANGEROUS_CHARS_PATTERN, v):
            raise ValueError("Word contains invalid characters")
        return v.strip()


# ---------------------------------------------------------------------------
# Response schemas — JSON string columns are automatically deserialized
# ---------------------------------------------------------------------------

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


class LyricDetailResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    title: str
    video_id: str
    language: str
    transcript: Any
    created_at: str
    updated_at: str

    @field_validator("transcript", mode="before")
    @classmethod
    def parse_transcript(cls, v: Any) -> Any:
        return json.loads(v) if isinstance(v, str) else v

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def datetime_to_str(cls, v: Any) -> str:
        return v.isoformat() if hasattr(v, "isoformat") else v


class SavedLyricListItem(BaseModel):
    id: str
    title: str
    language: str
    created_at: str
    updated_at: str


class ResourceDetailResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    title: str
    file_name: str
    file_type: str
    language: str
    transcript: Any
    media_file_path: Optional[str] = None
    created_at: str
    updated_at: str

    @field_validator("transcript", mode="before")
    @classmethod
    def parse_transcript(cls, v: Any) -> Any:
        return json.loads(v) if isinstance(v, str) else v

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def datetime_to_str(cls, v: Any) -> str:
        return v.isoformat() if hasattr(v, "isoformat") else v


class SavedResourceListItem(BaseModel):
    id: str
    title: str
    file_name: str
    language: str
    has_media: bool
    created_at: str
    updated_at: str


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


# ---------------------------------------------------------------------------
# Pagination wrapper
# ---------------------------------------------------------------------------

class PaginatedResponse(BaseModel):
    total: Optional[int] = None
    limit: Optional[int] = None
    offset: int = 0


# Keep legacy aliases so any other code referencing the old names still works
StoryResponse = StoryDetailResponse
LyricResponse = LyricDetailResponse
ResourceResponse = ResourceDetailResponse
VisualResponse = VisualDetailResponse

