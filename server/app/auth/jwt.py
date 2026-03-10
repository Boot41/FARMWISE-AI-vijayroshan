from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any, cast
from uuid import UUID, uuid4

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models import User
from app.db.session import get_db_session

if not hasattr(bcrypt, "__about__"):
    bcrypt.__about__ = SimpleNamespace(  # type: ignore[attr-defined]
        __version__=getattr(bcrypt, "__version__", "unknown")
    )

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    try:
        return cast(str, pwd_context.hash(password))
    except ValueError:
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        return hashed_password.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return cast(bool, pwd_context.verify(password, password_hash))
    except ValueError:
        return bool(bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8")))


def _create_token(subject: str, token_type: str, expires_delta: timedelta) -> tuple[str, datetime]:
    settings = get_settings()
    issued_at = datetime.now(UTC)
    expires_at = issued_at + expires_delta
    payload = {"sub": subject, "token_type": token_type, "exp": expires_at}
    payload["iat"] = issued_at
    payload["jti"] = str(uuid4())
    encoded = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    return encoded, expires_at


def create_access_token(subject: str) -> tuple[str, datetime]:
    settings = get_settings()
    return _create_token(
        subject=subject,
        token_type="access",
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(subject: str) -> tuple[str, datetime]:
    settings = get_settings()
    return _create_token(
        subject=subject,
        token_type="refresh",
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
    )


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        decoded_payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc

    if not isinstance(decoded_payload, dict):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    payload = cast(dict[str, Any], decoded_payload)

    subject = payload.get("sub")
    if not isinstance(subject, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
        )
    return payload


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )

    payload = decode_token(credentials.credentials)
    if payload.get("token_type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")
    try:
        user_id = UUID(payload["sub"])
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject"
        ) from exc

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
