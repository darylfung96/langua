from sqlalchemy import create_engine, Column, String, DateTime, Text, ForeignKey, Index, event, func
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session, relationship
from datetime import datetime, timezone
import uuid
import os
import logging

from config import DATABASE_URL, IS_PRODUCTION, DB_POOL_SIZE, DB_MAX_OVERFLOW, DB_POOL_RECYCLE, DB_POOL_TIMEOUT

logger = logging.getLogger(__name__)

_engine_kwargs: dict = {}
if DATABASE_URL.startswith("sqlite"):
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    _engine_kwargs["pool_size"] = DB_POOL_SIZE
    _engine_kwargs["max_overflow"] = DB_MAX_OVERFLOW
    _engine_kwargs["pool_recycle"] = DB_POOL_RECYCLE
    _engine_kwargs["pool_timeout"] = DB_POOL_TIMEOUT
    _engine_kwargs["pool_pre_ping"] = True  # Detect stale connections

# SQL query logging: warn if enabled in production, auto-disable by default
_sql_echo = os.getenv("SQL_ECHO", "false").lower() == "true"
if IS_PRODUCTION and _sql_echo:
    logger.warning("SQL_ECHO is enabled in production - this may impact performance and leak sensitive query data")
_engine_kwargs["echo"] = _sql_echo and not IS_PRODUCTION  # Auto-disable in prod

engine = create_engine(DATABASE_URL, **_engine_kwargs)

# SQLite does not enforce FK constraints by default — enable them on every connection.
if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, _connection_record):
        """Configure SQLite for better concurrency and reliability."""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")  # Enforce foreign keys
        cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging for better concurrency
        cursor.execute("PRAGMA synchronous=NORMAL")  # Balance safety vs speed
        cursor.execute("PRAGMA cache_size=10000")   # 10MB cache
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=True)   # NULL for Google-only accounts
    google_id = Column(String(255), unique=True, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False)

    stories = relationship("Story", cascade="all, delete-orphan", passive_deletes=True)
    lyrics = relationship("Lyric", cascade="all, delete-orphan", passive_deletes=True)
    resources = relationship("Resource", cascade="all, delete-orphan", passive_deletes=True)
    visuals = relationship("Visual", cascade="all, delete-orphan", passive_deletes=True)


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
    quiz = Column(Text, nullable=True)  # Stored as JSON string
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
    images = Column(Text, nullable=False)  # Stored as JSON string
    prompt = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=func.now(), onupdate=lambda: datetime.now(timezone.utc), nullable=False)


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
