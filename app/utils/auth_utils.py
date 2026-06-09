from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, status, Header
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session
from app.dao.user import UserDAO
from app.exceptions import AppException
from app.models import User
from app.schemas import ErrorCode, UserRole

import secrets

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

SECRET = settings.RANDOM_SECRET
ALGORITHM = "HS256"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta if expires_delta else timedelta(minutes=60))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET, algorithm=ALGORITHM)


async def get_current_user(
        authorization: Optional[str] = Header(None, alias="Authorization"),
        session: AsyncSession = Depends(get_session)
):
    credentials_exception = AppException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        error_code=ErrorCode.UNAUTHORIZED,
        detail="Токен отсутствует или невалиден"
    )

    if not authorization:
        raise credentials_exception

    try:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer":
            raise credentials_exception

        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except (JWTError, ValueError):
        raise credentials_exception

    user = await UserDAO.find_by_id(session, user_id)
    if user is None:
        raise credentials_exception
    return user

async def admin_only(current_user: User = Depends(get_current_user)) -> User:
    """Checks if the current user is an admin."""
    if current_user.role != UserRole.ADMIN:
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code=ErrorCode.FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

def create_refresh_token() -> str:
    return secrets.token_urlsafe(32)