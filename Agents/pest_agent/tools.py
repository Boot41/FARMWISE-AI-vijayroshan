from __future__ import annotations

import os
import re
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


def _normalise_region_lookup(value: str) -> str:
    cleaned = re.sub(r"^[a-z_ ]*:\s*", "", value.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"[^\w,\- ]+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,.-")
    return cleaned


async def get_pest_guide(crop: str) -> str:
    """
    Reads the pest and disease guide for a specific crop from local documents.

    Use this tool when you need to:
    - Identify what pest or disease matches the symptoms described
    - Find treatment options, organic alternatives, and prevention tips
    - Know which pests are common for the farmer's current crop

    Valid crop names: tomato, rice, wheat, onion, groundnut,
                     maize, bajra, mustard, pepper, coconut.
    Normalise the crop name to lowercase before calling.
    Returns the full markdown content of the pest guide.
    Returns an empty string if no guide exists for that crop.
    """
    crop_key = crop.strip().lower()
    guide_path = DOCS_DIR / "pest_guides" / f"{crop_key}.md"
    if not guide_path.exists():
        return ""
    return guide_path.read_text(encoding="utf-8")


async def get_pesticide_reference() -> str:
    """
    Reads the approved pesticide reference catalog from local documents.

    Use this tool when you need to:
    - Find the correct dosage for a recommended pesticide
    - Check pre-harvest waiting periods before recommending a spray
    - Find an approved organic alternative to a chemical pesticide
    - Verify that a pesticide is approved for use in India

    Returns the full markdown content of the approved pesticide catalog.
    """
    ref_path = DOCS_DIR / "pesticide_reference" / "approved_pesticides.md"
    if not ref_path.exists():
        return ""
    return ref_path.read_text(encoding="utf-8")


async def get_weather_forecast(region_id: str) -> list[dict]:
    """
    Fetches the 7-day weather forecast for the farmer's region from the database.

    Use this tool when you need to:
    - Warn the farmer not to spray pesticides before rain
    - Recommend the safest date to apply treatment
    - Check humidity levels that worsen fungal disease

    Accepts either a region UUID or a region label such as district,
    region_name, or state. Prefer passing the farmer's region_id.
    Returns up to 7 rows ordered by forecast_date ASC.
    Each row contains: forecast_date, min_temp, max_temp,
                       expected_rainfall_mm, humidity_pct.
    """
    conn = await asyncpg.connect(os.environ["DATABASE_URL"])
    try:
        resolved_region_id = region_id
        try:
            UUID(region_id)
        except (ValueError, TypeError, AttributeError):
            lookup_value = _normalise_region_lookup(region_id)
            if not lookup_value:
                return []

            region_row = await conn.fetchrow(
                """
                SELECT id
                FROM regions
                WHERE lower(region_name) = lower($1)
                   OR lower(district) = lower($1)
                   OR lower(state) = lower($1)
                LIMIT 1
                """,
                lookup_value,
            )
            if region_row is None:
                region_row = await conn.fetchrow(
                    """
                    SELECT id
                    FROM regions
                    WHERE lower($1) LIKE '%' || lower(region_name) || '%'
                       OR lower($1) LIKE '%' || lower(district) || '%'
                       OR lower($1) LIKE '%' || lower(state) || '%'
                       OR lower(region_name) LIKE '%' || lower($1) || '%'
                       OR lower(district) LIKE '%' || lower($1) || '%'
                       OR lower(state) LIKE '%' || lower($1) || '%'
                    ORDER BY
                        CASE
                            WHEN lower(district) = lower($1) THEN 0
                            WHEN lower(region_name) = lower($1) THEN 1
                            WHEN lower(state) = lower($1) THEN 2
                            ELSE 3
                        END,
                        region_name
                    LIMIT 1
                    """,
                    lookup_value,
                )
            if region_row is None:
                return []
            resolved_region_id = str(region_row["id"])

        rows = await conn.fetch(
            """
            SELECT
                forecast_date, min_temp, max_temp,
                expected_rainfall_mm, humidity_pct
            FROM weather_forecasts
            WHERE region_id = $1::uuid
            ORDER BY forecast_date ASC
            LIMIT 7
            """,
            resolved_region_id,
        )
        return [_serialize_row(row) for row in rows]
    finally:
        await conn.close()
