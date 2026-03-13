import os
import sys
import tempfile
import warnings
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# Database Configuration
# ============================================================================
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./stories.db")

# Detect if we're in production (explicit PRODUCTION env or non-SQLite URL)
IS_PRODUCTION = (
    os.getenv("PRODUCTION", "").lower() in ("true", "1", "yes") or
    (DATABASE_URL and not DATABASE_URL.startswith("sqlite"))
)

# Warn if using SQLite in production
if IS_PRODUCTION and DATABASE_URL.startswith("sqlite"):
    warnings.warn(
        "⚠️  Using SQLite in PRODUCTION is not recommended. "
        "SQLite does not handle concurrent writes well and lacks "
        "horizontal scalability. Please use PostgreSQL in production. "
        "Set DATABASE_URL to a PostgreSQL connection string to dismiss this warning.",
        UserWarning
    )

# Database Connection Pool Settings (for PostgreSQL, MySQL, etc.)
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))
DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "3600"))
DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))

# JWT Authentication
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET_KEY environment variable is not set. "
        "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
    )
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24h

# Google OAuth2
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# Gemini Configuration
GEMINI_COOKIE_1PSID = os.getenv("GEMINI_COOKIE_1PSID")
GEMINI_COOKIE_1PSIDTS = os.getenv("GEMINI_COOKIE_1PSIDTS", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # Official API key for audio generation and other features

# Model Configuration
WHISPER_MODEL_NAME = os.getenv("WHISPER_MODEL_NAME", "medium")
WHISPER_MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB

# Temp directory for intermediate file processing
TEMP_DIR = os.getenv("TEMP_DIR", tempfile.gettempdir())

# Request timeouts (seconds)
TRANSCRIBE_TIMEOUT = int(os.getenv("TRANSCRIBE_TIMEOUT", "300"))  # 5 minutes for audio transcription
AI_REQUEST_TIMEOUT = int(os.getenv("AI_REQUEST_TIMEOUT", "180"))    # 60 seconds for Gemini AI calls

# CORS Configuration — set CORS_ORIGINS env var as a comma-separated list for deployment
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

# ============================================================================
# CSRF Protection Settings
# ============================================================================
CSRF_COOKIE_NAME = os.getenv("CSRF_COOKIE_NAME", "csrf_token")
CSRF_HEADER_NAME = "X-CSRF-Token"
CSRF_TOKEN_LENGTH = 32  # bytes
CSRF_MAX_AGE = int(os.getenv("CSRF_MAX_AGE", "604800"))  # 7 days in seconds
# Secret for HMAC token hashing - MUST be different from JWT_SECRET_KEY
CSRF_SECRET = os.getenv("CSRF_SECRET", "")

# ============================================================================
# Logging Configuration
# ============================================================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.getenv("LOG_FORMAT", "development")  # "development" or "json"
