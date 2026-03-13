from pydantic import BaseModel
from typing import List, Optional


class VocabWord(BaseModel):
    word: str
    meaning_in_target: str
    equivalent_in_english: str


class StoryRequest(BaseModel):
    title: str
    story_content: str
    language: str
    vocabulary: str
    quiz: Optional[str] = None
    audio: Optional[str] = None


class StoryResponse(BaseModel):
    id: str
    title: str
    story_content: str
    language: str
    vocabulary: dict
    audio: Optional[str] = None
    created_at: str
    updated_at: str


class SavedStoryListItem(BaseModel):
    id: str
    title: str
    language: str
    created_at: str
    updated_at: str


class LyricRequest(BaseModel):
    title: str
    video_id: str
    language: str
    transcript: str


class LyricResponse(BaseModel):
    id: str
    title: str
    video_id: str
    language: str
    transcript: list
    created_at: str
    updated_at: str


class SavedLyricListItem(BaseModel):
    id: str
    title: str
    language: str
    created_at: str
    updated_at: str


class ResourceRequest(BaseModel):
    title: str
    file_name: str
    file_type: str
    language: str
    transcript: str
    media_file_path: Optional[str] = None


class ResourceResponse(BaseModel):
    id: str
    title: str
    file_name: str
    file_type: str
    language: str
    transcript: list
    media_file_path: Optional[str] = None
    created_at: str
    updated_at: str


class SavedResourceListItem(BaseModel):
    id: str
    title: str
    file_name: str
    language: str
    created_at: str
    updated_at: str


class VisualRequest(BaseModel):
    word: str
    language: str
    images: str  # JSON string
    prompt: str
    explanation: Optional[str] = None


class VisualResponse(BaseModel):
    id: str
    word: str
    language: str
    images: list
    prompt: str
    explanation: Optional[str] = None
    created_at: str
    updated_at: str


class SavedVisualListItem(BaseModel):
    id: str
    word: str
    language: str
    created_at: str
    updated_at: str
