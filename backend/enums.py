"""
Centralised enums for the application.

Using str-based enums ensures they serialise naturally to JSON strings
and can be stored directly in database columns without conversion.
"""
from enum import Enum


class WordMatchStatus(str, Enum):
    """Status of a word during a shadowing attempt."""
    PENDING = "pending"
    CURRENT = "current"
    MATCHED = "matched"
    MISSED = "missed"


class WordDifficulty(str, Enum):
    """Difficulty rating for a phrase word, set by the AI."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class QuestionType(str, Enum):
    """Type of quiz question generated for a story."""
    MULTIPLE_CHOICE = "multiple_choice"
    FILL_BLANK = "fill_blank"
    TRUE_FALSE = "true_false"


class MediaFileType(str, Enum):
    """Broadly categorised media types for uploaded resources."""
    AUDIO = "audio"
    VIDEO = "video"
