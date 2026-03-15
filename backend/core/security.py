from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
import logging

from config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_ACCESS_TOKEN_EXPIRE_MINUTES
from db import User, get_db

logger = logging.getLogger(__name__)

# auto_error=False so we can fall back to the cookie when no Bearer header is present
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

AUTH_COOKIE_NAME = "auth_token"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[str]:
    """Decode a JWT and return the user_id (sub), or None on failure."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


async def get_current_user(
    request: Request,
    bearer_token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the current user from an httpOnly cookie or Authorization: Bearer header.

    Also sets request.state.user_id for use by rate limiter and other middleware.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Prefer Bearer token for API clients; fall back to httpOnly cookie for browser sessions.
    token = bearer_token or request.cookies.get(AUTH_COOKIE_NAME)

    if not token:
        raise credentials_exception

    user_id = decode_token(token)
    if not user_id:
        logger.warning("Invalid JWT token attempt")
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    # Set user_id on request state for rate limiting and other uses
    request.state.user_id = user.id

    return user
