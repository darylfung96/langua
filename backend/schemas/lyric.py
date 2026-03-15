import json
from pydantic import BaseModel, field_validator, Field
from typing import Any

from constants import MAX_TITLE_LENGTH, MAX_LANGUAGE_LENGTH, MAX_VIDEO_ID_LENGTH
from schemas.common import validate_language
from core.utils import validate_video_id


class LyricRequest(BaseModel):
    title: str = Field(min_length=1, max_length=MAX_TITLE_LENGTH)
    video_id: str = Field(min_length=1, max_length=MAX_VIDEO_ID_LENGTH)
    language: str = Field(min_length=1, max_length=MAX_LANGUAGE_LENGTH)
    transcript: str = Field(min_length=2)  # at least "[]"

    @field_validator("language")
    @classmethod
    def validate_language_code(cls, v: str) -> str:
        return validate_language(v)

    @field_validator("video_id")
    @classmethod
    def validate_video_id_format(cls, v: str) -> str:
        if not validate_video_id(v):
            raise ValueError("Invalid YouTube video ID format")
        return v


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


# Legacy alias
LyricResponse = LyricDetailResponse
