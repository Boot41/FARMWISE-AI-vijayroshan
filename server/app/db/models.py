from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


json_type = JSON().with_variant(JSONB, "postgresql")


class Region(Base):
    __tablename__ = "regions"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    state: Mapped[str] = mapped_column(String(120), index=True)
    district: Mapped[str] = mapped_column(String(120), index=True)
    region_name: Mapped[str] = mapped_column(String(150), unique=True)
    dominant_soil_type: Mapped[str] = mapped_column(String(120))
    default_water_availability: Mapped[str] = mapped_column(String(120))
    climate_zone: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

    users: Mapped[list[User]] = relationship(back_populates="region")
    region_crops: Mapped[list[RegionCrop]] = relationship(
        back_populates="region", cascade="all, delete-orphan"
    )
    weather_forecasts: Mapped[list[WeatherForecast]] = relationship(
        back_populates="region", cascade="all, delete-orphan"
    )
    mandi_prices: Mapped[list[MandiPrice]] = relationship(
        back_populates="region", cascade="all, delete-orphan"
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(150))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone_number: Mapped[str | None] = mapped_column(String(30), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    region_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("regions.id", ondelete="RESTRICT"), index=True
    )
    water_availability: Mapped[str | None] = mapped_column(String(120), nullable=True)
    irrigation_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    current_crop: Mapped[str | None] = mapped_column(String(120), nullable=True)
    sowing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        server_default=func.now(),
    )

    region: Mapped[Region] = relationship(back_populates="users")
    chat_sessions: Mapped[list[ChatSession]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    refresh_tokens: Mapped[list[RefreshToken]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class RegionCrop(Base):
    __tablename__ = "region_crops"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    region_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("regions.id", ondelete="CASCADE"), index=True
    )
    crop_name: Mapped[str] = mapped_column(String(120))
    crop_season: Mapped[str] = mapped_column(String(30))
    suitability_score: Mapped[float] = mapped_column(Float)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

    region: Mapped[Region] = relationship(back_populates="region_crops")


class WeatherForecast(Base):
    __tablename__ = "weather_forecasts"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    region_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("regions.id", ondelete="CASCADE"), index=True
    )
    forecast_date: Mapped[date] = mapped_column(Date, index=True)
    min_temp: Mapped[float] = mapped_column(Float)
    max_temp: Mapped[float] = mapped_column(Float)
    expected_rainfall_mm: Mapped[float] = mapped_column(Float)
    humidity_pct: Mapped[float] = mapped_column(Float)
    wind_speed_kmph: Mapped[float] = mapped_column(Float)
    forecast_generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

    region: Mapped[Region] = relationship(back_populates="weather_forecasts")


class MandiPrice(Base):
    __tablename__ = "mandi_prices"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    region_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("regions.id", ondelete="CASCADE"), index=True
    )
    crop_name: Mapped[str] = mapped_column(String(120), index=True)
    price_per_quintal: Mapped[float] = mapped_column(Float)
    recorded_date: Mapped[date] = mapped_column(Date, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

    region: Mapped[Region] = relationship(back_populates="mandi_prices")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        server_default=func.now(),
    )

    user: Mapped[User] = relationship(back_populates="chat_sessions")
    messages: Mapped[list[ChatMessage]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(20))
    message_text: Mapped[str] = mapped_column(Text)
    message_metadata: Mapped[dict[str, object] | None] = mapped_column(json_type, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

    session: Mapped[ChatSession] = relationship(back_populates="messages")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    token: Mapped[str] = mapped_column(String(512), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

    user: Mapped[User] = relationship(back_populates="refresh_tokens")
