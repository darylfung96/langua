"""CSRF protection using double-submit cookie pattern with database-backed token storage."""
import asyncio
import secrets
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse

from config import CSRF_COOKIE_NAME, CSRF_HEADER_NAME, CSRF_TOKEN_LENGTH, CSRF_MAX_AGE, CSRF_SECRET, IS_PRODUCTION
from core.security import AUTH_COOKIE_NAME, decode_token
from db import get_db, CSRFToken

# We no longer use in-memory dict; all tokens are stored in the database

_csrf_cleanup_counter = 0
_CSRF_CLEANUP_INTERVAL = 100  # Run token cleanup every Nth protected request

def generate_csrf_token() -> str:
    """Generate a cryptographically secure CSRF token."""
    return secrets.token_urlsafe(CSRF_TOKEN_LENGTH)


def _hash_token(token: str) -> str:
    """HMAC-SHA256 hash of the token for storage (prevents token disclosure if store is leaked)."""
    return hmac.new(CSRF_SECRET.encode(), token.encode(), hashlib.sha256).hexdigest()


def validate_csrf_token(db, token: str, user_id: str) -> bool:
    """Validate a CSRF token for a given user by checking the database.

    Args:
        db: SQLAlchemy Session (synchronous)
        token: The raw CSRF token from the client
        user_id: Expected user ID

    Returns:
        True if valid, False otherwise
    """
    hashed = _hash_token(token)

    # Find token in database
    record = db.query(CSRFToken).filter(CSRFToken.token_hash == hashed).first()
    if not record:
        return False

    # Check user_id match
    if record.user_id != user_id:
        return False

    # Check expiration (use naive datetime to match SQLite storage)
    now = datetime.utcnow()
    if now > record.expires_at:
        # Token expired - delete it
        db.delete(record)
        db.commit()
        return False

    return True


async def issue_csrf_token(response: Response, user_id: str) -> str:
    """Create a new CSRF token, store in database, set cookie, and return token value."""
    from db import SessionLocal  # Import here to avoid circular import

    token = generate_csrf_token()
    hashed = _hash_token(token)
    expires_at = datetime.utcnow() + timedelta(seconds=CSRF_MAX_AGE)

    # Store in database
    db = SessionLocal()
    try:
        csrf_token = CSRFToken(
            token_hash=hashed,
            user_id=user_id,
            expires_at=expires_at
        )
        db.add(csrf_token)
        db.commit()
    except Exception as e:
        db.rollback()
        raise RuntimeError(f"Failed to store CSRF token: {e}")
    finally:
        db.close()

    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=token,
        httponly=False,  # Must be readable by JavaScript to send in header
        samesite="lax",
        secure=IS_PRODUCTION,
        max_age=CSRF_MAX_AGE,
        path="/",
    )
    return token


async def revoke_csrf_token(user_id: str) -> None:
    """Remove all CSRF tokens for a user (e.g., on logout)."""
    from db import SessionLocal

    db = SessionLocal()
    try:
        deleted = db.query(CSRFToken).filter(CSRFToken.user_id == user_id).delete()
        db.commit()
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()


def cleanup_expired_csrf_tokens(db, batch_size: int = 1000) -> int:
    """Delete expired CSRF tokens. Returns number of tokens deleted."""
    now = datetime.utcnow()
    deleted = (
        db.query(CSRFToken)
        .filter(CSRFToken.expires_at < now)
        .limit(batch_size)
        .delete(synchronize_session=False)
    )
    db.commit()
    return deleted


class CSRFMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce CSRF protection on state-changing requests."""

    async def dispatch(self, request: Request, call_next):
        # Skip CSRF check for safe methods (RFC 7231)
        if request.method in ["GET", "HEAD", "OPTIONS", "TRACE"]:
            return await call_next(request)

        # Skip certain endpoints like auth/login, auth/register (they need to be public)
        exempt_paths = [
            "/auth/login",
            "/auth/logout",
            "/auth/register",
            "/auth/google/callback",
            "/auth/google/token",
            "/health",
            "/health/live",
            "/health/ready",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]
        if any(request.url.path.startswith(path) for path in exempt_paths):
            return await call_next(request)

        # Extract CSRF token from header only (cookie fallback would defeat double-submit protection)
        csrf_token = request.headers.get(CSRF_HEADER_NAME)

        # Bearer token authentication is not vulnerable to CSRF (browsers cannot forge Authorization
        # headers cross-origin), so skip CSRF validation for API clients using Bearer tokens.
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return await call_next(request)

        if not csrf_token:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"success": False, "message": "CSRF token missing"}
            )

        # Validate token — extract user_id since auth middleware may not have run yet
        user_id = getattr(request.state, "user_id", None)
        if not user_id:
            token = request.cookies.get(AUTH_COOKIE_NAME)
            if not token:
                auth_header = request.headers.get("Authorization", "")
                if auth_header.startswith("Bearer "):
                    token = auth_header[7:]
            if token:
                user_id = decode_token(token)
        if not user_id:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"success": False, "message": "Authentication required"}
            )

        # Validate token against database
        from db import SessionLocal
        db = SessionLocal()
        try:
            valid = validate_csrf_token(db, csrf_token, user_id)
            # Occasionally clean up expired tokens
            global _csrf_cleanup_counter
            _csrf_cleanup_counter += 1
            if _csrf_cleanup_counter % _CSRF_CLEANUP_INTERVAL == 0:
                cleanup_expired_csrf_tokens(db)
        finally:
            db.close()

        if not valid:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"success": False, "message": "Invalid CSRF token"}
            )

        return await call_next(request)
