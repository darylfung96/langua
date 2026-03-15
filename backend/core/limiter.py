"""Shared SlowAPI rate limiter instance.

Import this module in main.py (to attach to the app) and in any route
module that needs per-endpoint limits.

Rate limiting strategy:
- Unauthenticated requests: limited by IP address
- Authenticated requests: limited by user ID (prevents IP-sharing attacks)
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request


def _get_rate_limit_key(request: Request) -> str:
    """
    Determine the rate limit key for a request.

    Prefer user ID if available (set by get_current_user dependency).
    Falls back to IP address for unauthenticated endpoints.
    """
    # Check if user_id was set by authentication middleware/dependency
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"
    # Fallback to IP-based limiting
    return get_remote_address(request)


limiter = Limiter(key_func=_get_rate_limit_key, default_limits=["60/minute"])
