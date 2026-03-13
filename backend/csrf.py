"""CSRF protection using double-submit cookie pattern."""
import secrets
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict

from fastapi import Request, Response, HTTPException, Depends, status
from starlette.middleware.base import BaseHTTPMiddleware

from fastapi.responses import JSONResponse

from config import CSRF_COOKIE_NAME, CSRF_HEADER_NAME, CSRF_TOKEN_LENGTH, CSRF_MAX_AGE, CSRF_SECRET
from security import AUTH_COOKIE_NAME, decode_token

# In-memory store for CSRF tokens (not scalable - use Redis in prod)
# Structure: {hashed_token: (user_id, expires_at)}
_csrf_tokens: Dict[str, tuple[str, datetime]] = {}


def generate_csrf_token() -> str:
    """Generate a cryptographically secure CSRF token."""
    return secrets.token_urlsafe(CSRF_TOKEN_LENGTH)


def _hash_token(token: str) -> str:
    """HMAC-SHA256 hash of the token for storage (prevents token disclosure if DB leaked)."""
    secret = CSRF_SECRET.encode() or b"development-secret-key-change-in-production"
    return hmac.new(secret, token.encode(), hashlib.sha256).hexdigest()


def validate_csrf_token(token: str, user_id: str) -> bool:
    """Validate a CSRF token for a given user."""
    hashed = _hash_token(token)
    if hashed not in _csrf_tokens:
        return False

    stored_user_id, expires_at = _csrf_tokens[hashed]
    if stored_user_id != user_id:
        return False

    if datetime.now(timezone.utc) > expires_at:
        del _csrf_tokens[hashed]
        return False

    return True


def issue_csrf_token(response: Response, user_id: str) -> str:
    """Create a new CSRF token, set cookie, and return token value."""
    token = generate_csrf_token()
    hashed = _hash_token(token)
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=CSRF_MAX_AGE)
    _csrf_tokens[hashed] = (user_id, expires_at)

    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=token,
        httponly=False,  # Must be readable by JavaScript to send in header
        samesite="lax",
        secure=False,  # Set to True in production via config
        max_age=CSRF_MAX_AGE,
        path="/",
    )
    return token


def revoke_csrf_token(user_id: str) -> None:
    """Remove all CSRF tokens for a user (e.g., on logout)."""
    to_remove = []
    for hashed, (stored_user_id, _) in _csrf_tokens.items():
        if stored_user_id == user_id:
            to_remove.append(hashed)
    for hashed in to_remove:
        del _csrf_tokens[hashed]


def cleanup_expired_tokens() -> None:
    """Remove expired tokens to prevent memory growth (call periodically)."""
    now = datetime.now(timezone.utc)
    expired = [hashed for hashed, (_, expires) in _csrf_tokens.items() if now > expires]
    for hashed in expired:
        del _csrf_tokens[hashed]


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

        # Extract CSRF token from header
        csrf_token = request.headers.get(CSRF_HEADER_NAME)
        if not csrf_token:
            # Also check cookie as fallback (double-submit pattern)
            csrf_token = request.cookies.get(CSRF_COOKIE_NAME)

        if not csrf_token:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"success": False, "message": "CSRF token missing"}
            )

        # Validate token — extract user_id directly since auth middleware may not have run yet
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

        if not validate_csrf_token(csrf_token, user_id):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"success": False, "message": "Invalid CSRF token"}
            )

        # Periodic cleanup of expired tokens (every 1000 requests is a reasonable default)
        # In production, use a separate scheduled task or Redis TTL
        if len(_csrf_tokens) > 10000:
            cleanup_expired_tokens()

        return await call_next(request)
