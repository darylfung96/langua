import json
import re
from pydantic import BaseModel, field_validator, Field
from typing import Any, List, Optional

from constants import (
    LANGUAGE_PATTERN,
    DANGEROUS_CHARS_PATTERN,
)
from core.sanitization import sanitize_html

_language_regex = re.compile(LANGUAGE_PATTERN)


def validate_language(v: str) -> str:
    """Validate language code format (BCP 47 basic). Shared across domain schemas."""
    if not v:
        raise ValueError("Language is required")
    if not _language_regex.match(v):
        raise ValueError(f"Invalid language format: {v}. Use format like 'en', 'en-US', 'zh-CN'")
    return v


class VocabWord(BaseModel):
    word: str
    meaning_in_target: str
    equivalent_in_english: str


class PaginatedResponse(BaseModel):
    total: Optional[int] = None
    limit: Optional[int] = None
    offset: int = 0
