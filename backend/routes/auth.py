"""
Authentication endpoints: register, login, and Google OAuth2.
"""
import logging
import secrets
import time
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    FRONTEND_URL,
)
from database import User, get_db
from schemas import UserRegister, Token, UserResponse
from security import hash_password, verify_password, create_access_token, get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

MIN_PASSWORD_LENGTH = 8

_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

# Short-lived one-time codes: {code -> (jwt_token, expires_at)}
# Codes expire after 5 minutes and are consumed on first use.
_PENDING_OAUTH_CODES: dict[str, tuple[str, float]] = {}
_OAUTH_CODE_TTL_SECONDS = 300


# ---------------------------------------------------------------------------
# Email / password
# ---------------------------------------------------------------------------

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Create a new user account."""
    if len(user_data.password) < MIN_PASSWORD_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Password must be at least {MIN_PASSWORD_LENGTH} characters",
        )

    existing = db.query(User).filter(User.email == user_data.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = User(
        email=user_data.email.lower(),
        hashed_password=hash_password(user_data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f"New user registered: {user.email}")
    return UserResponse.model_validate(user)


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Authenticate with email/password and return a JWT access token."""
    user = db.query(User).filter(User.email == form_data.username.lower()).first()
    if not user or not user.hashed_password or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token({"sub": user.id, "email": user.email})
    return Token(access_token=token)


# ---------------------------------------------------------------------------
# Google OAuth2
# ---------------------------------------------------------------------------

@router.get("/google/login")
async def google_login():
    """Redirect the browser to Google's OAuth2 consent screen."""
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured on this server.",
        )
    params = urlencode({
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
    })
    return RedirectResponse(f"{_GOOGLE_AUTH_URL}?{params}")


@router.get("/google/callback")
async def google_callback(code: str, db: Session = Depends(get_db)):
    """Exchange the Google authorization code for a JWT and redirect to the frontend."""
    # Exchange code for Google access token
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(_GOOGLE_TOKEN_URL, data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        })

    if token_resp.status_code != 200:
        logger.error(f"Google token exchange failed: {token_resp.text}")
        return RedirectResponse(f"{FRONTEND_URL}/login?error=google_auth_failed")

    google_tokens = token_resp.json()
    access_token = google_tokens.get("access_token")

    # Fetch user profile from Google
    async with httpx.AsyncClient() as client:
        userinfo_resp = await client.get(
            _GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )

    if userinfo_resp.status_code != 200:
        return RedirectResponse(f"{FRONTEND_URL}/login?error=google_userinfo_failed")

    userinfo = userinfo_resp.json()
    google_id: str = userinfo.get("id", "")
    email: str = userinfo.get("email", "").lower()

    if not email:
        return RedirectResponse(f"{FRONTEND_URL}/login?error=no_email")

    # Find or create user
    user = db.query(User).filter(User.email == email).first()
    if user:
        # Link google_id if not already set
        if not user.google_id:
            user.google_id = google_id
            db.commit()
    else:
        user = User(email=email, google_id=google_id, hashed_password=None)
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"New user created via Google OAuth: {email}")

    jwt_token = create_access_token({"sub": user.id, "email": user.email})

    # Use a short-lived one-time code instead of putting the JWT in the URL.
    # This prevents the token from appearing in browser history, server logs, or Referer headers.
    code = secrets.token_urlsafe(32)
    _PENDING_OAUTH_CODES[code] = (jwt_token, time.monotonic() + _OAUTH_CODE_TTL_SECONDS)
    return RedirectResponse(f"{FRONTEND_URL}/login?code={code}")


@router.get("/google/token", response_model=Token)
async def google_exchange_code(code: str):
    """Exchange a one-time OAuth code for a JWT access token."""
    entry = _PENDING_OAUTH_CODES.pop(code, None)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired code")
    jwt_token, expires_at = entry
    if time.monotonic() > expires_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired code")
    return Token(access_token=jwt_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Return the authenticated user's profile."""
    return UserResponse.model_validate(current_user)
