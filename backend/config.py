import hashlib
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

# Google Cloud Text-to-Speech — optional; falls back to browser TTS when not set.
# Free tier: 1M Standard chars/month, 4M WaveNet chars/month.
GOOGLE_CLOUD_TTS_API_KEY = os.getenv("GOOGLE_CLOUD_TTS_API_KEY")
TTS_REQUEST_TIMEOUT = float(os.getenv("TTS_REQUEST_TIMEOUT", "30"))  # seconds per TTS API call
TTS_SPEAKING_RATE = float(os.getenv("TTS_SPEAKING_RATE", "0.9"))     # 0.25–4.0; 0.9 = slightly slow for learners

# Model Configuration
WHISPER_MODEL_NAME = os.getenv("WHISPER_MODEL_NAME", "medium")
WHISPER_MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB

# Temp directory for intermediate file processing
TEMP_DIR = os.getenv("TEMP_DIR", tempfile.gettempdir())

# Uploads directory - store media files outside the codebase for persistence
# Default: './uploads' (relative to backend). Override with absolute path for production.
UPLOADS_DIR = os.getenv("UPLOADS_DIR", os.path.join(os.path.dirname(__file__), "uploads"))

# Auto-initialize database on startup (convenience for development)
# Default: true in development, false in production.
# Set AUTO_INIT_DB=false to prevent create_all() on startup (use migrations instead)
_auto_init_default = "false" if IS_PRODUCTION else "true"
AUTO_INIT_DB = os.getenv("AUTO_INIT_DB", _auto_init_default).lower() in ("true", "1", "yes")

# Log a warning if AUTO_INIT_DB is enabled in production (potential schema drift risk)
if AUTO_INIT_DB and IS_PRODUCTION:
    warnings.warn(
        "AUTO_INIT_DB is enabled in production. This may cause schema drift. "
        "Use Alembic migrations and set AUTO_INIT_DB=false for production deployments.",
        UserWarning
    )

# Request timeouts (seconds)
TRANSCRIBE_TIMEOUT = int(os.getenv("TRANSCRIBE_TIMEOUT", "300"))  # 5 minutes for audio transcription
AI_REQUEST_TIMEOUT = int(os.getenv("AI_REQUEST_TIMEOUT", "180"))    # 60 seconds for Gemini AI calls

# CORS Configuration — set CORS_ORIGINS env var as a comma-separated list for deployment
# Default includes both HTTP and HTTPS for localhost to support development with SSL
DEFAULT_CORS_ORIGINS = "http://localhost:5173,https://localhost:5173"
CORS_ORIGINS = os.getenv("CORS_ORIGINS", DEFAULT_CORS_ORIGINS).split(",")

# HTTPS/SSL Configuration for the server (uvicorn)
# These are NOT standard SSL_* env vars to avoid interfering with outbound SSL
SERVER_SSL_CERT_FILE = os.getenv("SERVER_SSL_CERT_FILE")
SERVER_SSL_KEY_FILE = os.getenv("SERVER_SSL_KEY_FILE")

# ============================================================================
# CSRF Protection Settings
# ============================================================================
CSRF_COOKIE_NAME = os.getenv("CSRF_COOKIE_NAME", "csrf_token")
CSRF_HEADER_NAME = "X-CSRF-Token"
CSRF_TOKEN_LENGTH = 32  # bytes
CSRF_MAX_AGE = int(os.getenv("CSRF_MAX_AGE", "604800"))  # 7 days in seconds
# Secret for HMAC token hashing — MUST be different from JWT_SECRET_KEY.
# Derive from JWT_SECRET_KEY if not explicitly set, so it's always strong.
CSRF_SECRET = os.getenv("CSRF_SECRET") or hashlib.sha256(
    f"csrf-secret:{JWT_SECRET_KEY}".encode()
).hexdigest()
if not os.getenv("CSRF_SECRET") and IS_PRODUCTION:
    warnings.warn(
        "CSRF_SECRET is not set explicitly. Set CSRF_SECRET in your environment for production.",
        UserWarning,
    )

# ============================================================================
# Logging Configuration
# ============================================================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.getenv("LOG_FORMAT", "development")  # "development" or "json"
