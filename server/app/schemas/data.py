from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RegionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    state: str
    district: str
    region_name: str
    dominant_soil_type: str
    default_water_availability: str
    climate_zone: str
    created_at: datetime


class RegionCropOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    region_id: UUID
    crop_name: str
    crop_season: str
    suitability_score: float
    notes: str | None
    created_at: datetime


class WeatherForecastOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    region_id: UUID
    forecast_date: date
    min_temp: float
    max_temp: float
    expected_rainfall_mm: float
    humidity_pct: float
    wind_speed_kmph: float
    forecast_generated_at: datetime
    created_at: datetime


class MandiPriceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    region_id: UUID
    crop_name: str
    price_per_quintal: float
    recorded_date: date
    created_at: datetime
