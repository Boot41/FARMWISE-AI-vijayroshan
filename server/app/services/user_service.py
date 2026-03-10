from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import User


async def get_user_profile(db: AsyncSession, *, user_id: UUID) -> User:
    result = await db.execute(
        select(User).options(selectinload(User.region)).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


async def update_user_profile(
    db: AsyncSession,
    *,
    user_id: UUID,
    water_availability: str | None,
    irrigation_type: str | None,
    current_crop: str | None,
) -> User:
    user = await get_user_profile(db, user_id=user_id)
    user.water_availability = water_availability
    user.irrigation_type = irrigation_type
    user.current_crop = current_crop
    await db.commit()
    return await get_user_profile(db, user_id=user_id)
