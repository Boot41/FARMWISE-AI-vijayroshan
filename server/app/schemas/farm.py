from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.data import RegionOut


class UserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: str
    phone_number: str | None
    region_id: UUID
    water_availability: str | None
    irrigation_type: str | None
    current_crop: str | None
    sowing_date: date | None
    created_at: datetime
    updated_at: datetime


class UserProfile(UserSummary):
    region: RegionOut


class UserProfileUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    water_availability: str | None = Field(default=None, max_length=120)
    irrigation_type: str | None = Field(default=None, max_length=120)
    current_crop: str | None = Field(default=None, max_length=120)
    sowing_date: date | None = None
