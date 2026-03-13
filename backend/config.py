import os
from dotenv import load_dotenv

load_dotenv()

# Database
DATABASE_URL = "sqlite:///./stories.db"

# API Keys
WHISPER_API_KEY = os.getenv("WHISPER_API_KEY")
if not WHISPER_API_KEY:
    raise RuntimeError("WHISPER_API_KEY environment variable is not set.")

# Gemini Configuration
GEMINI_COOKIE_1PSID = os.getenv("GEMINI_COOKIE_1PSID")
GEMINI_COOKIE_1PSIDTS = os.getenv("GEMINI_COOKIE_1PSIDTS", "")

# Model Configuration
WHISPER_MODEL_NAME = "medium"
WHISPER_MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB

# CORS Configuration
CORS_ORIGINS = ["http://localhost:5173"]
