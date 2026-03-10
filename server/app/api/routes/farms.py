from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_session
from app.middleware.auth_middleware import CurrentUser
from app.schemas.common import APIResponse
from app.schemas.farm import UserProfile, UserProfileUpdateRequest
from app.services.user_service import get_user_profile, update_user_profile

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=APIResponse[UserProfile])
async def get_me(
    current_user: CurrentUser,
    db: AsyncSession = Depends(db_session),
) -> APIResponse[UserProfile]:
    user = await get_user_profile(db, user_id=current_user.id)
    return APIResponse(
        message="User profile fetched successfully", data=UserProfile.model_validate(user)
    )


@router.patch("/me", response_model=APIResponse[UserProfile])
async def patch_me(
    body: UserProfileUpdateRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(db_session),
) -> APIResponse[UserProfile]:
    user = await update_user_profile(
        db,
        user_id=current_user.id,
        water_availability=body.water_availability,
        irrigation_type=body.irrigation_type,
        current_crop=body.current_crop,
        sowing_date=body.sowing_date,
    )
    return APIResponse(
        message="User profile updated successfully", data=UserProfile.model_validate(user)
    )
