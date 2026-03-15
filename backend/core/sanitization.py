"""HTML sanitization utilities using bleach library with XSS protection.

This module centralizes all HTML sanitization logic to prevent XSS attacks
when user-generated content is rendered in the frontend.
"""
import logging
import re

logger = logging.getLogger(__name__)

try:
    import bleach
    BLEACH_AVAILABLE = True
except ImportError:
    BLEACH_AVAILABLE = False
    logger.warning("bleach library not installed; HTML sanitization will use fallback regex (less secure)")


def sanitize_html(v: str) -> str:
    """Sanitize HTML content to prevent XSS attacks.

    Uses the bleach library when available for robust HTML filtering.
    Falls back to regex-based sanitization if bleach is not installed.

    Allowed tags: basic formatting (b, i, u, em, strong, p, br, span)
    Allowed attributes on span: class, title (for vocabulary highlighting)

    Args:
        v: Raw HTML string

    Returns:
        Sanitized HTML string safe for rendering
    """
    if not v:
        return v

    if BLEACH_AVAILABLE:
        try:
            allowed_tags = ['b', 'i', 'u', 'em', 'strong', 'p', 'br', 'span']
            allowed_attributes = {
                'span': ['class', 'title']
            }
            return bleach.clean(
                v,
                tags=allowed_tags,
                attributes=allowed_attributes,
                strip=True,
                strip_comments=True
            )
        except Exception as e:
            logger.error(f"Bleach sanitization failed, falling back to regex: {e}")

    # Fallback: regex-based sanitization (less secure but better than nothing)
    return _fallback_sanitize(v)


def _fallback_sanitize(v: str) -> str:
    """Regex-based fallback sanitization when bleach is not available."""
    # Remove script tags and content
    v = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', v, flags=re.IGNORECASE | re.DOTALL)
    # Remove event handlers (onclick, onerror, etc.)
    v = re.sub(r'\s+on\w+\s*=\s*["\'][^"\']*["\']', '', v, flags=re.IGNORECASE)
    # Remove javascript: and data: URLs in href/src attributes (common XSS vectors)
    v = re.sub(r'\s+(?:href|src)\s*=\s*["\'][^"\']*(?:javascript:|data:|file:|vbscript:)[^"\']*["\']', '', v, flags=re.IGNORECASE)
    # Remove other dangerous protocols
    v = re.sub(r'javascript\s*:', '', v, flags=re.IGNORECASE)
    return v
