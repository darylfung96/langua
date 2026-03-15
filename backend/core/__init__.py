"""
core package — cross-cutting infrastructure (security, CSRF, rate limiting,
sanitization, file storage, shared utilities).

Re-exports the most-used symbols for convenient ``from core import X`` access.
"""
from core.security import (  # noqa: F401
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from core.limiter import limiter  # noqa: F401
from core.sanitization import sanitize_html  # noqa: F401
from core.utils import (  # noqa: F401
    format_timestamp,
    extract_video_id,
    validate_video_id,
    generate_creative_prompt,
    success_response,
    error_response,
    api_success,
    api_error,
)
