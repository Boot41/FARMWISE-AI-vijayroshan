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


async def get_mandi_prices(region_id: str, crop_name: str | None = None) -> list[dict]:
    """
    Fetches the last 7 days of mandi prices for the farmer's region.

    Use this tool when you need to:
    - Know the current price for a crop at the local mandi
    - Calculate whether prices are trending up or down over the past week
    - Compare today's price against the 7-day average

    crop_name is optional. If provided, filters to that crop only.
    If omitted, returns prices for all crops in the region.
    Returns up to 7 rows per crop ordered by recorded_date DESC
    (most recent first).
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
    - Find the seasonal market outlook for a crop
    - Check government schemes or MSP information for the season
    - Understand near-term price direction from expert forecasts

    Valid seasons: kharif, rabi.
    Valid years: 2024 (expand as new advisories are added).
    Normalise season to lowercase.
    Returns the full markdown content of the advisory.
    Returns an empty string if no advisory exists for that season and year.
    """
    season_key = season.strip().lower()
    advisory_path = DOCS_DIR / "advisories" / f"{season_key}_{year}.md"
    if not advisory_path.exists():
        return ""
    return advisory_path.read_text(encoding="utf-8")
