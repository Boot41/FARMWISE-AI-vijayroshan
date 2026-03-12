from __future__ import annotations

import os
from datetime import date
from pathlib import Path
from uuid import UUID

import asyncpg
from dotenv import load_dotenv

load_dotenv()

DOCS_DIR = Path(__file__).parent.parent / "docs"


def _serialize_row(row) -> dict:
    if row is None:
        return {}
    result = {}
    for key, value in dict(row).items():
        if isinstance(value, (UUID, date)):
            result[key] = str(value)
        else:
            result[key] = value
    return result


def _normalize_lookup_value(value: str) -> str:
    return value.strip().lower()


async def _resolve_region_id(conn: asyncpg.Connection, region_id: str) -> str | None:
    try:
        return str(UUID(region_id))
    except (ValueError, TypeError, AttributeError):
        pass

    lookup_value = _normalize_lookup_value(region_id)
    if not lookup_value:
        return None

    resolved = await conn.fetchval(
        """
        SELECT id
        FROM regions
        WHERE LOWER(district) = $1
           OR LOWER(state) = $1
           OR LOWER(region_name) = $1
        ORDER BY created_at ASC
        LIMIT 1
        """,
        lookup_value,
    )
    if resolved is None:
        return None
    return str(resolved)


async def get_region_crops(region_id: str) -> list[dict]:
    """
    Fetches the crops suitable for the farmer's region with suitability scores.

    Use this tool when you need to:
    - Know which crops grow well in the farmer's specific region
    - Compare suitability scores to shortlist the best agronomic options
    - Filter by season (Kharif, Rabi, Zaid) to match the planting window

    Returns all crops for the region ordered by suitability_score DESC.
    Each row contains: crop_name, crop_season, suitability_score.
    """
    conn = await asyncpg.connect(os.environ["DATABASE_URL"])
    try:
        resolved_region_id = await _resolve_region_id(conn, region_id)
        if resolved_region_id is None:
            return []

        rows = await conn.fetch(
            """
            SELECT crop_name, crop_season, suitability_score
            FROM region_crops
            WHERE region_id = $1::uuid
            ORDER BY suitability_score DESC
            """,
            resolved_region_id,
        )
        return [_serialize_row(row) for row in rows]
    finally:
        await conn.close()


async def get_crop_calendar(state: str) -> str:
    """
    Reads the crop calendar for a given Indian state from local documents.

    Use this tool when you need to:
    - Find the correct sowing window for a recommended crop
    - Find the expected harvest window and duration
    - Know the water and input requirements per crop per state

    Valid state names: kerala, maharashtra, punjab, rajasthan, tamil_nadu.
    Normalise to lowercase and replace spaces with underscores.
    Returns the full markdown content of the crop calendar.
    Returns an empty string if no calendar exists for that state.
    """
    state_key = state.strip().lower().replace(" ", "_")
    calendar_path = DOCS_DIR / "crop_calendars" / f"{state_key}.md"
    if not calendar_path.exists():
        return ""
    return calendar_path.read_text(encoding="utf-8")


async def get_mandi_prices(region_id: str, crop_name: str | None = None) -> list[dict]:
    """
    Fetches the last 7 days of mandi prices for the farmer's region.

    Use this tool when you need to:
    - Check the current market price for a candidate crop
    - Estimate revenue based on expected yield and current price
    - Compare prices across multiple crops to find the most profitable option

    crop_name is optional. If omitted, returns prices for all crops in the region.
    Returns up to 7 rows per crop ordered by recorded_date DESC.
    Each row contains: crop_name, price_per_quintal, recorded_date.
    """
    conn = await asyncpg.connect(os.environ["DATABASE_URL"])
    try:
        resolved_region_id = await _resolve_region_id(conn, region_id)
        if resolved_region_id is None:
            return []

        if crop_name:
            rows = await conn.fetch(
                """
                SELECT crop_name, price_per_quintal, recorded_date
                FROM mandi_prices
                WHERE region_id = $1::uuid
                  AND LOWER(crop_name) = LOWER($2)
                ORDER BY recorded_date DESC
                LIMIT 7
                """,
                resolved_region_id,
                crop_name,
            )
        else:
            rows = await conn.fetch(
                """
                SELECT crop_name, price_per_quintal, recorded_date
                FROM mandi_prices
                WHERE region_id = $1::uuid
                ORDER BY recorded_date DESC
                LIMIT 7
                """,
                resolved_region_id,
            )
        return [_serialize_row(row) for row in rows]
    finally:
        await conn.close()


async def get_advisory(season: str, year: int) -> str:
    """
    Reads the seasonal crop advisory from local documents.

    Use this tool when you need to:
    - Find which crops are recommended for the coming season
    - Check the seasonal market outlook to filter economically viable options
    - Find government scheme or subsidy information relevant to crop choice

    Valid seasons: kharif, rabi.
    Valid years: 2026.
    Normalise season to lowercase.
    Returns the full markdown content of the advisory.
    Returns an empty string if no advisory exists for that season and year.
    """
    season_key = season.strip().lower()
    advisory_path = DOCS_DIR / "advisories" / f"{season_key}_{year}.md"
    if not advisory_path.exists():
        return ""
    return advisory_path.read_text(encoding="utf-8")
