from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Index, Integer, Float, func
from sqlalchemy.orm import DeclarativeBase, relationship
from datetime import datetime, timezone
import uuid


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=True)   # NULL for Google-only accounts
    google_id = Column(String(255), unique=True, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False)
    failed_login_attempts = Column(Integer, default=0, server_default="0", nullable=False)
    locked_until = Column(DateTime, nullable=True)

    stories = relationship("Story", cascade="all, delete-orphan", passive_deletes=True)
    lyrics = relationship("Lyric", cascade="all, delete-orphan", passive_deletes=True)
    resources = relationship("Resource", cascade="all, delete-orphan", passive_deletes=True)
    visuals = relationship("Visual", cascade="all, delete-orphan", passive_deletes=True)
    shadowing_sessions = relationship("ShadowingSession", cascade="all, delete-orphan", passive_deletes=True)


class Story(Base):
    __tablename__ = "stories"
    __table_args__ = (
        Index('ix_stories_user_created', 'user_id', 'created_at'),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    story_content = Column(Text, nullable=False)
    language = Column(String(100), nullable=False)
    vocabulary = Column(Text, nullable=False)  # Stored as JSON string
    quiz = Column(Text, nullable=True)          # Stored as JSON string
    audio_file_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now(), onupdate=lambda: datetime.now(timezone.utc), nullable=False)


class Lyric(Base):
    __tablename__ = "lyrics"
    __table_args__ = (
        Index('ix_lyrics_user_created', 'user_id', 'created_at'),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    video_id = Column(String(100), nullable=False)
    language = Column(String(100), nullable=False)
    transcript = Column(Text, nullable=False)  # Stored as JSON string
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now(), onupdate=lambda: datetime.now(timezone.utc), nullable=False)


class Resource(Base):
    __tablename__ = "resources"
    __table_args__ = (
        Index('ix_resources_user_created', 'user_id', 'created_at'),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(100), nullable=False)
    language = Column(String(100), nullable=False)
    transcript = Column(Text, nullable=False)  # Stored as JSON string
    media_file_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now(), onupdate=lambda: datetime.now(timezone.utc), nullable=False)


class Visual(Base):
    __tablename__ = "visuals"
    __table_args__ = (
        Index('ix_visuals_user_created', 'user_id', 'created_at'),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    word = Column(String(255), nullable=False)
    language = Column(String(100), nullable=False)
    images = Column(Text, nullable=False)       # Stored as JSON string
    prompt = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now(), onupdate=lambda: datetime.now(timezone.utc), nullable=False)


class ShadowingSession(Base):
    __tablename__ = "shadowing_sessions"
    __table_args__ = (
        Index('ix_shadowing_sessions_user_created', 'user_id', 'created_at'),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    theme = Column(String(255), nullable=False)
    language = Column(String(100), nullable=False, server_default='en')
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)

    attempts = relationship("ShadowingAttempt", cascade="all, delete-orphan", passive_deletes=True)


class ShadowingAttempt(Base):
    __tablename__ = "shadowing_attempts"
    __table_args__ = (
        Index('ix_shadowing_attempts_session', 'session_id', 'attempted_at'),
        Index('ix_shadowing_attempts_session_phrase', 'session_id', 'phrase_id'),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("shadowing_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    phrase_id = Column(Integer, nullable=False)
    phrase_text = Column(Text, nullable=False)
    accuracy_score = Column(Float, nullable=False, server_default='0.0')
    words_matched = Column(Integer, nullable=False, server_default='0')
    total_words = Column(Integer, nullable=False, server_default='0')
    attempted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False)


class CSRFToken(Base):
    """CSRF tokens stored in database for validation and revocation."""
    __tablename__ = "csrf_tokens"

    token_hash = Column(String(64), primary_key=True)  # SHA256 hash of the token
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False)


class OAuthCode(Base):
    """One-time OAuth exchange codes stored in database."""
    __tablename__ = "oauth_codes"

    code = Column(String(64), primary_key=True)  # The one-time code (sha256 hash or token)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    jwt_token = Column(Text, nullable=False)      # The JWT to be exchanged
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False)
