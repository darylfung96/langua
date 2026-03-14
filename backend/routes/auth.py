"""
Authentication endpoints: register, login, and Google OAuth2.
"""
import asyncio
import logging
import secrets
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from slowapi.util import get_remote_address
from jose import jwt
import time
import secrets

from config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    FRONTEND_URL,
    IS_PRODUCTION,
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
)
from database import User, get_db, OAuthCode
from schemas import UserRegister, Token, UserResponse
from security import (
    AUTH_COOKIE_NAME,
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
    get_current_user,
)
from limiter import limiter
from csrf import issue_csrf_token, revoke_csrf_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

MIN_PASSWORD_LENGTH = 8
_COOKIE_MAX_AGE = JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60  # seconds

# Account lockout settings
_MAX_FAILED_ATTEMPTS = 5
_LOCKOUT_DURATION = timedelta(minutes=15)
# Pre-computed dummy hash for timing normalization on login (prevents user enumeration).
# Computed once at startup so login response time is consistent whether user exists or not.
_DUMMY_HASH = hash_password("dummy-timing-normalization-constant")

_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

# OAuth codes stored in database (short-lived one-time codes)
# Codes expire after 5 minutes and are consumed on first use.
_OAUTH_CODE_TTL_SECONDS = 300
_MAX_PENDING_OAUTH_CODES = 10_000


def _cleanup_expired_oauth_codes(db: Session) -> int:
    """Delete expired OAuth codes from database. Returns count of deleted codes."""
    now = datetime.now(timezone.utc)
    deleted = (
        db.query(OAuthCode)
        .filter(OAuthCode.expires_at < now)
        .delete(synchronize_session=False)
    )
    db.commit()
    return deleted


def _set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",      # "strict" breaks OAuth redirects; "lax" is safe for same-origin
        secure=IS_PRODUCTION,
        max_age=_COOKIE_MAX_AGE,
        path="/",
    )


# ---------------------------------------------------------------------------
# Email / password
# ---------------------------------------------------------------------------

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/hour", key_func=get_remote_address)  # Stricter IP-based limit
async def register(request: Request, user_data: UserRegister, db: Session = Depends(get_db)):
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
    logger.info(f"New user registered (id: {user.id})")
    return UserResponse.model_validate(user)


@router.post("/login")
@limiter.limit("15/minute", key_func=get_remote_address)  # IP-based limit for login
async def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Authenticate with email/password, set an httpOnly cookie, and return user info with CSRF token."""
    now = datetime.now(timezone.utc)
    user = db.query(User).filter(User.email == form_data.username.lower()).first()

    # Check account lockout (do this before verifying password to avoid timing oracle)
    if user and user.locked_until:
        locked_until = user.locked_until
        # Make locked_until timezone-aware if stored as naive datetime
        if locked_until.tzinfo is None:
            locked_until = locked_until.replace(tzinfo=timezone.utc)
        if now < locked_until:
            remaining = int((locked_until - now).total_seconds() / 60) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Account temporarily locked. Try again in {remaining} minute(s).",
            )
        # Lockout expired — clear it
        user.failed_login_attempts = 0
        user.locked_until = None
        db.commit()

    # Always call verify_password to normalize timing regardless of whether the user exists.
    # This prevents timing-based user enumeration (bcrypt is slow; skipping it leaks account existence).
    stored_hash = user.hashed_password if (user and user.hashed_password) else _DUMMY_HASH
    password_ok = verify_password(form_data.password, stored_hash)
    credentials_bad = not user or not user.hashed_password or not password_ok
    if credentials_bad:
        if user:
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            if user.failed_login_attempts >= _MAX_FAILED_ATTEMPTS:
                user.locked_until = now + _LOCKOUT_DURATION
                logger.warning(f"Account locked after too many failed attempts (id: {user.id})")
            db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Successful login — reset failure counter
    if user.failed_login_attempts:
        user.failed_login_attempts = 0
        user.locked_until = None
        db.commit()

    token = create_access_token({"sub": user.id, "email": user.email})
    _set_auth_cookie(response, token)

    # Issue CSRF token for the frontend
    csrf_token = await issue_csrf_token(response, user.id)

    # Return both token and CSRF token
    return Token(access_token=token, csrf_token=csrf_token)


@router.post("/logout")
async def logout(response: Response, request: Request):
    """Clear the auth cookie and CSRF token."""
    # Revoke CSRF tokens for this user
    user_id = decode_token(request.cookies.get(AUTH_COOKIE_NAME))
    if user_id:
        await revoke_csrf_token(user_id)

    response.delete_cookie(key=AUTH_COOKIE_NAME, path="/")
    response.delete_cookie(key="csrf_token", path="/")
    return {"message": "Logged out"}


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

    user = db.query(User).filter(User.email == email).first()
    if user:
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
    # Store the code in database with expiration
    exchange_code = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=_OAUTH_CODE_TTL_SECONDS)

    db = SessionLocal()
    try:
        # Cleanup expired codes occasionally
        _cleanup_expired_oauth_codes(db)

        # Check store size and prune if needed
        pending_count = db.query(OAuthCode).count()
        if pending_count >= _MAX_PENDING_OAUTH_CODES:
            logger.warning("OAuth code store is full; dropping oldest codes")
            oldest = (
                db.query(OAuthCode)
                .order_by(OAuthCode.created_at.asc())
                .limit(100)
                .all()
            )
            for old in oldest:
                db.delete(old)
            db.commit()

        # Store new code
        oauth_code = OAuthCode(
            code=exchange_code,
            user_id=user.id,
            jwt_token=jwt_token,
            expires_at=expires_at
        )
        db.add(oauth_code)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to store OAuth code: {e}")
        # Continue anyway - user can retry
    finally:
        db.close()

    return RedirectResponse(f"{FRONTEND_URL}/login?code={exchange_code}")


@router.get("/google/token")
async def google_exchange_code(code: str, response: Response):
    """Exchange a one-time OAuth code for a JWT access token, set as httpOnly cookie."""
    db = SessionLocal()
    try:
        # Find the OAuth code
        entry = db.query(OAuthCode).filter(OAuthCode.code == code).first()
        if entry is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired code")

        # Check expiration
        now = datetime.now(timezone.utc)
        if now > entry.expires_at:
            db.delete(entry)
            db.commit()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired code")

        jwt_token = entry.jwt_token
        user_id = entry.user_id

        # Delete the code after use (one-time use)
        db.delete(entry)
        db.commit()
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error exchanging OAuth code: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
    finally:
        db.close()

    # Decode token to get user_id (we could extract from jwt_token directly)
    from jose import jwt
    from config import JWT_SECRET_KEY, JWT_ALGORITHM
    try:
        payload = jwt.decode(jwt_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id_from_token = payload.get("sub")
        # Use user_id from token if available, otherwise from DB entry
        user_id = user_id_from_token or user_id
    except Exception:
        # Token should be valid; if not, still proceed with DB user_id
        pass

    _set_auth_cookie(response, jwt_token)

    # Issue CSRF token if we have user_id
    if user_id:
        csrf_token = await issue_csrf_token(response, user_id)
    else:
        csrf_token = None

    return Token(access_token=jwt_token, csrf_token=csrf_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Return the authenticated user's profile."""
    return UserResponse.model_validate(current_user)
