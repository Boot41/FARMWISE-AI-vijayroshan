"""create farmwise schema

Revision ID: 20260310_0001
Revises:
Create Date: 2026-03-10 00:01:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260310_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "regions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("state", sa.String(length=120), nullable=False),
        sa.Column("district", sa.String(length=120), nullable=False),
        sa.Column("region_name", sa.String(length=150), nullable=False),
        sa.Column("dominant_soil_type", sa.String(length=120), nullable=False),
        sa.Column("default_water_availability", sa.String(length=120), nullable=False),
        sa.Column("climate_zone", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("region_name"),
    )
    op.create_index(op.f("ix_regions_district"), "regions", ["district"], unique=False)
    op.create_index(op.f("ix_regions_state"), "regions", ["state"], unique=False)

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone_number", sa.String(length=30), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("region_id", sa.Uuid(), nullable=False),
        sa.Column("water_availability", sa.String(length=120), nullable=True),
        sa.Column("irrigation_type", sa.String(length=120), nullable=True),
        sa.Column("current_crop", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["region_id"], ["regions.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_region_id"), "users", ["region_id"], unique=False)

    op.create_table(
        "region_crops",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("region_id", sa.Uuid(), nullable=False),
        sa.Column("crop_name", sa.String(length=120), nullable=False),
        sa.Column("crop_season", sa.String(length=30), nullable=False),
        sa.Column("suitability_score", sa.Float(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["region_id"], ["regions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_region_crops_region_id"), "region_crops", ["region_id"], unique=False)

    op.create_table(
        "weather_forecasts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("region_id", sa.Uuid(), nullable=False),
        sa.Column("forecast_date", sa.Date(), nullable=False),
        sa.Column("min_temp", sa.Float(), nullable=False),
        sa.Column("max_temp", sa.Float(), nullable=False),
        sa.Column("expected_rainfall_mm", sa.Float(), nullable=False),
        sa.Column("humidity_pct", sa.Float(), nullable=False),
        sa.Column("wind_speed_kmph", sa.Float(), nullable=False),
        sa.Column("forecast_generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["region_id"], ["regions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_weather_forecasts_forecast_date"), "weather_forecasts", ["forecast_date"], unique=False)
    op.create_index(op.f("ix_weather_forecasts_region_id"), "weather_forecasts", ["region_id"], unique=False)

    op.create_table(
        "mandi_prices",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("region_id", sa.Uuid(), nullable=False),
        sa.Column("crop_name", sa.String(length=120), nullable=False),
        sa.Column("price_per_quintal", sa.Float(), nullable=False),
        sa.Column("recorded_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["region_id"], ["regions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_mandi_prices_crop_name"), "mandi_prices", ["crop_name"], unique=False)
    op.create_index(op.f("ix_mandi_prices_recorded_date"), "mandi_prices", ["recorded_date"], unique=False)
    op.create_index(op.f("ix_mandi_prices_region_id"), "mandi_prices", ["region_id"], unique=False)

    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_chat_sessions_user_id"), "chat_sessions", ["user_id"], unique=False)

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("message_text", sa.Text(), nullable=False),
        sa.Column("message_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["chat_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_chat_messages_session_id"), "chat_messages", ["session_id"], unique=False)

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token", sa.String(length=512), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )
    op.create_index(op.f("ix_refresh_tokens_token"), "refresh_tokens", ["token"], unique=True)
    op.create_index(op.f("ix_refresh_tokens_user_id"), "refresh_tokens", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_refresh_tokens_user_id"), table_name="refresh_tokens")
    op.drop_index(op.f("ix_refresh_tokens_token"), table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
    op.drop_index(op.f("ix_chat_messages_session_id"), table_name="chat_messages")
    op.drop_table("chat_messages")
    op.drop_index(op.f("ix_chat_sessions_user_id"), table_name="chat_sessions")
    op.drop_table("chat_sessions")
    op.drop_index(op.f("ix_mandi_prices_region_id"), table_name="mandi_prices")
    op.drop_index(op.f("ix_mandi_prices_recorded_date"), table_name="mandi_prices")
    op.drop_index(op.f("ix_mandi_prices_crop_name"), table_name="mandi_prices")
    op.drop_table("mandi_prices")
    op.drop_index(op.f("ix_weather_forecasts_region_id"), table_name="weather_forecasts")
    op.drop_index(op.f("ix_weather_forecasts_forecast_date"), table_name="weather_forecasts")
    op.drop_table("weather_forecasts")
    op.drop_index(op.f("ix_region_crops_region_id"), table_name="region_crops")
    op.drop_table("region_crops")
    op.drop_index(op.f("ix_users_region_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    op.drop_index(op.f("ix_regions_state"), table_name="regions")
    op.drop_index(op.f("ix_regions_district"), table_name="regions")
    op.drop_table("regions")
