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


async def get_crop_calendar(state: str) -> str:
    """
    Reads the crop calendar for a given Indian state from local documents.

    Use this tool when you need to:
    - Know the growth stages for the farmer's current crop
    - Find water requirements per growth stage
    - Calculate what stage the crop is in based on days since sowing

    Valid state names: kerala, maharashtra, punjab, rajasthan, tamil_nadu.
    Normalise the state name to lowercase and replace spaces with underscores.
    Returns the full markdown content of the crop calendar.
    Returns an empty string if no calendar exists for that state.
    """
    state_key = state.strip().lower().replace(" ", "_")
    calendar_path = DOCS_DIR / "crop_calendars" / f"{state_key}.md"
    if not calendar_path.exists():
        return ""
    return calendar_path.read_text(encoding="utf-8")


async def get_weather_forecast(region_id: str) -> list[dict]:
    """
    Fetches the 7-day weather forecast for the farmer's region from the database.

    Use this tool when you need to:
    - Identify days with significant rainfall to skip irrigation
    - Check if rain will cover the crop's water needs for that day
    - Plan the irrigation schedule around upcoming weather

    Returns up to 7 rows ordered by forecast_date ASC.
    Each row contains: forecast_date, min_temp, max_temp,
                       expected_rainfall_mm, humidity_pct.
    Treat any day with expected_rainfall_mm >= 10 as a skip day.
    """
    conn = await asyncpg.connect(os.environ["DATABASE_URL"])
    try:
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
            region_id,
        )
        return [_serialize_row(row) for row in rows]
    finally:
        await conn.close()
