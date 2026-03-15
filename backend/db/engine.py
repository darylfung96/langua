from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
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
    logger.warning(
        "SQL_ECHO is enabled in production - this may impact performance and leak sensitive query data"
    )
_engine_kwargs["echo"] = _sql_echo and not IS_PRODUCTION  # Auto-disable in prod

engine = create_engine(DATABASE_URL, **_engine_kwargs)

# SQLite does not enforce FK constraints by default — enable them on every connection.
if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, _connection_record):
        """Configure SQLite for better concurrency and reliability."""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")   # Enforce foreign keys
        cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging for better concurrency
        cursor.execute("PRAGMA synchronous=NORMAL")  # Balance safety vs speed
        cursor.execute("PRAGMA cache_size=10000")    # 10MB cache
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
