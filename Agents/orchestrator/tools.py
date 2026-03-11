from __future__ import annotations

import os
from datetime import date
from uuid import UUID

import asyncpg

DEMO_USER_ALIASES = {
    "demo-user-1": "meera@farmwise.ai",
}


def _serialize_row(row: asyncpg.Record | None) -> dict:
    if row is None:
        return {}

    serialized: dict[str, object] = {}
    for key, value in dict(row).items():
        if isinstance(value, (UUID, date)):
            serialized[key] = str(value)
        else:
            serialized[key] = value
    return serialized


async def get_user_context(user_id: str) -> dict:
    """
    Fetches the farmer's profile and region information from the database.

    Use this tool when you need to:
    - Know what crop the farmer is currently growing
    - Know the farmer's region, soil type, or irrigation setup
    - Personalise your advice to this specific farmer

    Returns: name, current_crop, sowing_date, irrigation_type,
             water_availability, region_id, state, district, region_name,
             dominant_soil_type, climate_zone.
    Never returns: email, password_hash, phone_number.
    """

    conn = await asyncpg.connect(os.environ["DATABASE_URL"])
    try:
        row = await conn.fetchrow(
            """
            SELECT
                u.id, u.name, u.current_crop, u.sowing_date, u.region_id,
                u.irrigation_type, u.water_availability,
                r.state, r.district, r.region_name,
                r.dominant_soil_type, r.climate_zone
            FROM users u
            JOIN regions r ON u.region_id = r.id
            WHERE u.id = $1::uuid
            """,
            user_id,
        )
        if row:
            return _serialize_row(row)

        demo_email = DEMO_USER_ALIASES.get(user_id)
        if not demo_email:
            return {}

        demo_row = await conn.fetchrow(
            """
            SELECT
                u.id, u.name, u.current_crop, u.sowing_date, u.region_id,
                u.irrigation_type, u.water_availability,
                r.state, r.district, r.region_name,
                r.dominant_soil_type, r.climate_zone
            FROM users u
            JOIN regions r ON u.region_id = r.id
            WHERE u.email = $1
            """,
            demo_email,
        )
        return _serialize_row(demo_row)
    except (ValueError, asyncpg.DataError):
        demo_email = DEMO_USER_ALIASES.get(user_id)
        if not demo_email:
            return {}

        demo_row = await conn.fetchrow(
            """
            SELECT
                u.id, u.name, u.current_crop, u.sowing_date, u.region_id,
                u.irrigation_type, u.water_availability,
                r.state, r.district, r.region_name,
                r.dominant_soil_type, r.climate_zone
            FROM users u
            JOIN regions r ON u.region_id = r.id
            WHERE u.email = $1
            """,
            demo_email,
        )
        return _serialize_row(demo_row)
    finally:
        await conn.close()
