"""
db package — SQLAlchemy engine, session, and ORM models.

Re-exports everything that was previously at the top level of database.py
so all existing imports continue to work after the split:

    from db import Base, engine, SessionLocal, get_db
    from db import User, Story, Lyric, Resource, Visual
    from db import ShadowingSession, ShadowingAttempt, CSRFToken, OAuthCode
"""
from db.engine import engine, SessionLocal, get_db
from db.models import (
    Base,
    User,
    Story,
    Lyric,
    Resource,
    Visual,
    ShadowingSession,
    ShadowingAttempt,
    CSRFToken,
    OAuthCode,
)


def init_db() -> None:
    """Create all database tables. Called from main.py lifespan on startup."""
    Base.metadata.create_all(bind=engine)


__all__ = [
    "engine",
    "SessionLocal",
    "get_db",
    "init_db",
    "Base",
    "User",
    "Story",
    "Lyric",
    "Resource",
    "Visual",
    "ShadowingSession",
    "ShadowingAttempt",
    "CSRFToken",
    "OAuthCode",
]
