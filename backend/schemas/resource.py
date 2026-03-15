import json
from pydantic import BaseModel, field_validator, Field
from typing import Any, Optional

from constants import MAX_TITLE_LENGTH, MAX_LANGUAGE_LENGTH, MAX_FILE_NAME_LENGTH, MAX_FILE_TYPE_LENGTH
from schemas.common import validate_language


class ResourceRequest(BaseModel):
    title: str = Field(min_length=1, max_length=MAX_TITLE_LENGTH)
    file_name: str = Field(min_length=1, max_length=MAX_FILE_NAME_LENGTH)
    file_type: str = Field(min_length=1, max_length=MAX_FILE_TYPE_LENGTH)
    language: str = Field(min_length=1, max_length=MAX_LANGUAGE_LENGTH)
    transcript: str = Field(min_length=2)  # at least "[]"
    media_file_path: Optional[str] = None

    @field_validator("language")
    @classmethod
    def validate_language_code(cls, v: str) -> str:
        return validate_language(v)

    @field_validator("file_name")
    @classmethod
    def validate_file_name(cls, v: str) -> str:
        if '..' in v or '/' in v or '\\' in v:
            raise ValueError("Invalid file name")
        return v


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


# Legacy alias
ResourceResponse = ResourceDetailResponse
