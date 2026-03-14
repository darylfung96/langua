"""Shared constants for the application to prevent drift between validation layers."""

# Database column length constraints
MAX_EMAIL_LENGTH = 255
MAX_PASSWORD_HASH_LENGTH = 255
MAX_GOOGLE_ID_LENGTH = 255
MAX_TITLE_LENGTH = 500
MAX_FILE_NAME_LENGTH = 255
MAX_FILE_TYPE_LENGTH = 100
MAX_LANGUAGE_LENGTH = 100
MAX_WORD_LENGTH = 200
MAX_PROMPT_LENGTH = 5000
MAX_EXPLANATION_LENGTH = 10000
MAX_STORY_CONTENT_LENGTH = 100000
MAX_VIDEO_ID_LENGTH = 50

# JSON field limits
MAX_JSON_STRING_LENGTH = 2000000  # 2MB for serialized JSON

# Upload limits
MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB
# Base64-encoded audio stored in DB (approx 1.37× binary size, so 50MB binary → ~68.5MB base64)
MAX_AUDIO_BASE64_LENGTH = int(MAX_UPLOAD_BYTES * 1.4)  # ~70_000_000

# Validation patterns
LANGUAGE_PATTERN = r'^[a-zA-Z]{2,3}(?:-[a-zA-Z]{2})?$'  # BCP 47 basic
# Pattern to detect HTML/script dangerous characters (used across validators)
DANGEROUS_CHARS_PATTERN = r'[<>"\'&]'

# Rate limiting
DEFAULT_RATE_LIMIT = "60/minute"
AUTH_REGISTER_LIMIT = "10/hour"
AUTH_LOGIN_LIMIT = "15/minute"

# Supported language codes (BCP 47) with their display names
LANGUAGE_NAMES: dict[str, str] = {
    'ar': 'Arabic',
    'de': 'German',
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
    'it': 'Italian',
    'ja': 'Japanese',
    'ko': 'Korean',
    'pt': 'Portuguese',
    'ru': 'Russian',
    'zh-CN': 'Chinese (Simplified)',
    'zh-TW': 'Chinese (Traditional)',
}
