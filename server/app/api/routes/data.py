from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_session
from app.schemas.common import APIResponse
from app.schemas.data import MandiPriceOut, RegionCropOut, RegionOut, WeatherForecastOut
from app.services.data_service import list_latest_mandi_prices, list_latest_weather, list_region_crops, list_regions

router = APIRouter(prefix="/data", tags=["data"])


@router.get("/regions", response_model=APIResponse[list[RegionOut]])
async def get_regions(db: AsyncSession = Depends(db_session)) -> APIResponse[list[RegionOut]]:
    regions = await list_regions(db)
    return APIResponse(
        message="Regions fetched successfully",
        data=[RegionOut.model_validate(region) for region in regions],
    )


@router.get("/regions/{region_id}/weather", response_model=APIResponse[list[WeatherForecastOut]])
async def get_region_weather(
    region_id: UUID,
    db: AsyncSession = Depends(db_session),
) -> APIResponse[list[WeatherForecastOut]]:
    weather = await list_latest_weather(db, region_id)
    return APIResponse(
        message="Weather forecast fetched successfully",
        data=[WeatherForecastOut.model_validate(item) for item in weather],
    )


@router.get("/regions/{region_id}/prices", response_model=APIResponse[list[MandiPriceOut]])
async def get_region_prices(
    region_id: UUID,
    db: AsyncSession = Depends(db_session),
) -> APIResponse[list[MandiPriceOut]]:
    prices = await list_latest_mandi_prices(db, region_id)
    return APIResponse(
        message="Mandi prices fetched successfully",
        data=[MandiPriceOut.model_validate(item) for item in prices],
    )


@router.get("/regions/{region_id}/crops", response_model=APIResponse[list[RegionCropOut]])
async def get_region_crops(
    region_id: UUID,
    db: AsyncSession = Depends(db_session),
) -> APIResponse[list[RegionCropOut]]:
    crops = await list_region_crops(db, region_id)
    return APIResponse(
        message="Regional crops fetched successfully",
        data=[RegionCropOut.model_validate(item) for item in crops],
    )
