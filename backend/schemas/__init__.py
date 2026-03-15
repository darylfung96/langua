"""
schemas package — Pydantic request/response models split by domain.

Re-exports everything that was previously in the monolithic schemas.py so
all existing ``from schemas import …`` statements continue to work unchanged.
"""
from schemas.common import VocabWord, PaginatedResponse, validate_language
from schemas.auth import UserRegister, UserLogin, Token, UserResponse
from schemas.story import (
    StoryRequest,
    StoryDetailResponse,
    SavedStoryListItem,
    StoryResponse,
)
from schemas.lyric import (
    LyricRequest,
    LyricDetailResponse,
    SavedLyricListItem,
    LyricResponse,
)
from schemas.resource import (
    ResourceRequest,
    ResourceDetailResponse,
    SavedResourceListItem,
    ResourceResponse,
)
from schemas.visual import (
    VisualRequest,
    VisualDetailResponse,
    SavedVisualListItem,
    VisualResponse,
)
from schemas.shadowing import (
    GeneratePhrasesRequest,
    StartSessionRequest,
    RecordAttemptRequest,
    TTSRequest,
)

__all__ = [
    # common
    "VocabWord",
    "PaginatedResponse",
    "validate_language",
    # auth
    "UserRegister",
    "UserLogin",
    "Token",
    "UserResponse",
    # story
    "StoryRequest",
    "StoryDetailResponse",
    "SavedStoryListItem",
    "StoryResponse",
    # lyric
    "LyricRequest",
    "LyricDetailResponse",
    "SavedLyricListItem",
    "LyricResponse",
    # resource
    "ResourceRequest",
    "ResourceDetailResponse",
    "SavedResourceListItem",
    "ResourceResponse",
    # visual
    "VisualRequest",
    "VisualDetailResponse",
    "SavedVisualListItem",
    "VisualResponse",
    # shadowing
    "GeneratePhrasesRequest",
    "StartSessionRequest",
    "RecordAttemptRequest",
    "TTSRequest",
]
