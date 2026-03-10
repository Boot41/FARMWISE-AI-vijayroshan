from __future__ import annotations

from fastapi import APIRouter

from app.schemas.common import APIResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=APIResponse[dict[str, str]])
async def health() -> APIResponse[dict[str, str]]:
    return APIResponse(message="FarmWise backend is healthy", data={"status": "ok"})
