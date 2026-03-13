import json
from pydantic import BaseModel, field_validator, EmailStr, Field
from typing import Any, List, Optional

# Maximum base64-encoded audio size (~67 MB encodes to ~90 MB base64)
_MAX_AUDIO_B64_CHARS = 90_000_000


class VocabWord(BaseModel):
    word: str
    meaning_in_target: str
    equivalent_in_english: str


# ---------------------------------------------------------------------------
# Auth schemas
# ---------------------------------------------------------------------------

class UserRegister(BaseModel):
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


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
    title: str = Field(min_length=1, max_length=500)
    story_content: str = Field(min_length=1, max_length=100_000)
    language: str = Field(min_length=1, max_length=100)
    vocabulary: str = Field(min_length=2)  # at least "[]"
    quiz: Optional[str] = None
    audio: Optional[str] = Field(default=None, max_length=_MAX_AUDIO_B64_CHARS)


class LyricRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    video_id: str = Field(min_length=1, max_length=50)
    language: str = Field(min_length=1, max_length=100)
    transcript: str = Field(min_length=2)  # at least "[]"


class ResourceRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    file_name: str = Field(min_length=1, max_length=255)
    file_type: str = Field(min_length=1, max_length=100)
    language: str = Field(min_length=1, max_length=100)
    transcript: str = Field(min_length=2)  # at least "[]"
    media_file_path: Optional[str] = None


class VisualRequest(BaseModel):
    word: str = Field(min_length=1, max_length=200)
    language: str = Field(min_length=1, max_length=100)
    images: str = Field(min_length=2)  # at least "[]"
    prompt: str = Field(min_length=1, max_length=5_000)
    explanation: Optional[str] = Field(default=None, max_length=10_000)


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

