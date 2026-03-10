from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import MandiPrice, Region, RegionCrop, WeatherForecast


async def get_region_or_404(db: AsyncSession, region_id: UUID) -> Region:
    result = await db.execute(select(Region).where(Region.id == region_id))
    region = result.scalar_one_or_none()
    if region is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Region not found")
    return region


async def list_regions(db: AsyncSession) -> Sequence[Region]:
    result = await db.execute(select(Region).order_by(Region.state, Region.district))
    return result.scalars().all()


async def list_region_crops(db: AsyncSession, region_id: UUID) -> Sequence[RegionCrop]:
    await get_region_or_404(db, region_id)
    result = await db.execute(
        select(RegionCrop)
        .where(RegionCrop.region_id == region_id)
        .order_by(desc(RegionCrop.suitability_score), RegionCrop.crop_name)
    )
    return result.scalars().all()


async def list_latest_weather(db: AsyncSession, region_id: UUID, limit: int = 7) -> list[WeatherForecast]:
    await get_region_or_404(db, region_id)
    result = await db.execute(
        select(WeatherForecast)
        .where(WeatherForecast.region_id == region_id)
        .order_by(desc(WeatherForecast.forecast_date), desc(WeatherForecast.created_at))
        .limit(limit)
    )
    forecasts = list(result.scalars().all())
    forecasts.sort(key=lambda forecast: forecast.forecast_date)
    return forecasts


async def list_latest_mandi_prices(db: AsyncSession, region_id: UUID) -> list[MandiPrice]:
    await get_region_or_404(db, region_id)
    result = await db.execute(
        select(MandiPrice)
        .where(MandiPrice.region_id == region_id)
        .order_by(MandiPrice.crop_name, desc(MandiPrice.recorded_date), desc(MandiPrice.created_at))
    )
    latest_by_crop: dict[str, MandiPrice] = {}
    for price in result.scalars():
        latest_by_crop.setdefault(price.crop_name, price)
    return sorted(latest_by_crop.values(), key=lambda item: item.crop_name)
