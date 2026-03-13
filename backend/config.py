import os
import tempfile
from dotenv import load_dotenv

load_dotenv()

# Database — override with a production URL (e.g. postgresql+psycopg2://...) via env var
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./stories.db")

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

# Model Configuration
WHISPER_MODEL_NAME = os.getenv("WHISPER_MODEL_NAME", "medium")
WHISPER_MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB

# Temp directory for intermediate file processing
TEMP_DIR = os.getenv("TEMP_DIR", tempfile.gettempdir())

# CORS Configuration — set CORS_ORIGINS env var as a comma-separated list for deployment
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
