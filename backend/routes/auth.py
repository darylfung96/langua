"""
Authentication endpoints: register, login, and Google OAuth2.
"""
import logging
import secrets
import time
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from slowapi.util import get_remote_address
from jose import jwt

from config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    FRONTEND_URL,
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
)
from database import User, get_db
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

_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

# Short-lived one-time codes: {code -> (jwt_token, expires_at)}
# Codes expire after 5 minutes and are consumed on first use.
# NOTE: In-memory store only works with a single worker process.  Use Redis for multi-worker deployments.
_PENDING_OAUTH_CODES: dict[str, tuple[str, float]] = {}
_OAUTH_CODE_TTL_SECONDS = 300
_MAX_PENDING_OAUTH_CODES = 10_000


def _cleanup_expired_oauth_codes() -> None:
    """Remove expired codes to prevent unbounded memory growth."""
    now = time.monotonic()
    expired = [code for code, (_, exp) in _PENDING_OAUTH_CODES.items() if now > exp]
    for code in expired:
        del _PENDING_OAUTH_CODES[code]


def _set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",      # "strict" breaks OAuth redirects; "lax" is safe for same-origin
        secure=False,        # Set to True in production (requires HTTPS)
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
    logger.info(f"New user registered: {user.email}")
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
    user = db.query(User).filter(User.email == form_data.username.lower()).first()
    if not user or not user.hashed_password or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token({"sub": user.id, "email": user.email})
    _set_auth_cookie(response, token)

    # Issue CSRF token for the frontend
    csrf_token = issue_csrf_token(response, user.id)

    # Return both token and CSRF token
    return Token(access_token=token, csrf_token=csrf_token)


@router.post("/logout")
async def logout(response: Response, request: Request):
    """Clear the auth cookie and CSRF token."""
    # Revoke CSRF tokens for this user
    user_id = decode_token(request.cookies.get(AUTH_COOKIE_NAME))
    if user_id:
        revoke_csrf_token(user_id)

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
    _cleanup_expired_oauth_codes()
    if len(_PENDING_OAUTH_CODES) >= _MAX_PENDING_OAUTH_CODES:
        logger.warning("OAuth code store is full; dropping oldest codes")
        oldest = sorted(_PENDING_OAUTH_CODES, key=lambda k: _PENDING_OAUTH_CODES[k][1])
        for k in oldest[:100]:
            del _PENDING_OAUTH_CODES[k]

    exchange_code = secrets.token_urlsafe(32)
    _PENDING_OAUTH_CODES[exchange_code] = (jwt_token, time.monotonic() + _OAUTH_CODE_TTL_SECONDS)
    return RedirectResponse(f"{FRONTEND_URL}/login?code={exchange_code}")


@router.get("/google/token")
async def google_exchange_code(code: str, response: Response):
    """Exchange a one-time OAuth code for a JWT access token, set as httpOnly cookie."""
    _cleanup_expired_oauth_codes()
    entry = _PENDING_OAUTH_CODES.pop(code, None)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired code")
    jwt_token, expires_at = entry
    if time.monotonic() > expires_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired code")

    # Decode token to get user_id (we could extract from the jwt_token itself)
    # Since we don't want to verify signature just to extract user_id, we'll trust it's valid from our context
    # Actually, we need to decode it properly:
    from jose import jwt
    from config import JWT_SECRET_KEY, JWT_ALGORITHM
    try:
        payload = jwt.decode(jwt_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
    except Exception:
        user_id = None

    _set_auth_cookie(response, jwt_token)

    # Issue CSRF token if we have user_id
    if user_id:
        csrf_token = issue_csrf_token(response, user_id)
    else:
        csrf_token = None

    return Token(access_token=jwt_token, csrf_token=csrf_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Return the authenticated user's profile."""
    return UserResponse.model_validate(current_user)
