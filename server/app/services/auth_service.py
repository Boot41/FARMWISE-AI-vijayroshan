from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.models import RefreshToken, Region, User
from app.schemas.auth import AccessTokenOnly, AuthPayload, TokenPair
from app.schemas.farm import UserSummary


async def _store_refresh_token(
    db: AsyncSession,
    *,
    user_id: UUID,
    token: str,
    expires_at: datetime,
) -> None:
    db.add(RefreshToken(user_id=user_id, token=token, expires_at=expires_at))
    await db.commit()


async def _build_auth_payload(db: AsyncSession, user: User) -> AuthPayload:
    access_token, _ = create_access_token(str(user.id))
    refresh_token, refresh_expires_at = create_refresh_token(str(user.id))
    await _store_refresh_token(
        db,
        user_id=user.id,
        token=refresh_token,
        expires_at=refresh_expires_at,
    )
    return AuthPayload(
        tokens=TokenPair(access_token=access_token, refresh_token=refresh_token),
        user=UserSummary.model_validate(user),
    )


async def register_user(
    db: AsyncSession,
    *,
    name: str,
    email: str,
    password: str,
    phone_number: str | None,
    region_id: UUID,
) -> AuthPayload:
    normalized_email = email.lower()
    existing_user = await db.execute(select(User).where(User.email == normalized_email))
    if existing_user.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")

    region_result = await db.execute(select(Region).where(Region.id == region_id))
    region = region_result.scalar_one_or_none()
    if region is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Region not found")

    user = User(
        name=name,
        email=normalized_email,
        phone_number=phone_number,
        password_hash=hash_password(password),
        region_id=region.id,
        water_availability=region.default_water_availability,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return await _build_auth_payload(db, user)


async def login_user(db: AsyncSession, *, email: str, password: str) -> AuthPayload:
    normalized_email = email.lower()
    result = await db.execute(select(User).where(User.email == normalized_email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    return await _build_auth_payload(db, user)


async def refresh_access_token(db: AsyncSession, *, refresh_token: str) -> AccessTokenOnly:
    payload = decode_token(refresh_token)
    if payload.get("token_type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    result = await db.execute(select(RefreshToken).where(RefreshToken.token == refresh_token))
    stored_token = result.scalar_one_or_none()
    if stored_token is None or stored_token.revoked:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is invalid")
    expires_at = stored_token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at < datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has expired")

    access_token, _ = create_access_token(str(payload["sub"]))
    return AccessTokenOnly(access_token=access_token)


async def logout_user(db: AsyncSession, *, refresh_token: str) -> None:
    result = await db.execute(select(RefreshToken).where(RefreshToken.token == refresh_token))
    stored_token = result.scalar_one_or_none()
    if stored_token is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Refresh token not found")
    stored_token.revoked = True
    await db.commit()
