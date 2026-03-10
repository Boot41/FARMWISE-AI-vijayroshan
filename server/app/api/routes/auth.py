from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_session
from app.schemas.auth import (
    AccessTokenOnly,
    AuthPayload,
    LoginRequest,
    LogoutRequest,
    RefreshTokenRequest,
    RegisterRequest,
)
from app.schemas.common import APIResponse, MessageAck
from app.services.auth_service import login_user, logout_user, refresh_access_token, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register", response_model=APIResponse[AuthPayload], status_code=status.HTTP_201_CREATED
)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(db_session),
) -> APIResponse[AuthPayload]:
    payload = await register_user(
        db,
        name=body.name,
        email=body.email,
        password=body.password,
        phone_number=body.phone_number,
        region_id=body.region_id,
    )
    return APIResponse(message="User registered successfully", data=payload)


@router.post("/login", response_model=APIResponse[AuthPayload])
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(db_session),
) -> APIResponse[AuthPayload]:
    payload = await login_user(db, email=body.email, password=body.password)
    return APIResponse(message="Login successful", data=payload)


@router.post("/refresh", response_model=APIResponse[AccessTokenOnly])
async def refresh(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(db_session),
) -> APIResponse[AccessTokenOnly]:
    payload = await refresh_access_token(db, refresh_token=body.refresh_token)
    return APIResponse(message="Access token refreshed", data=payload)


@router.post("/logout", response_model=APIResponse[MessageAck])
async def logout(
    body: LogoutRequest,
    db: AsyncSession = Depends(db_session),
) -> APIResponse[MessageAck]:
    await logout_user(db, refresh_token=body.refresh_token)
    return APIResponse(message="Refresh token revoked", data=MessageAck(detail="Logout completed"))
