from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.db.models import Region, User


@pytest.mark.asyncio
async def test_data_endpoints_and_profile_updates(
    client: AsyncClient,
    seeded_region: Region,
    seeded_user: User,
    auth_headers: dict[str, str],
) -> None:
    regions_response = await client.get("/api/data/regions")
    assert regions_response.status_code == 200
    assert len(regions_response.json()["data"]) == 1

    weather_response = await client.get(f"/api/data/regions/{seeded_region.id}/weather")
    assert weather_response.status_code == 200
    assert len(weather_response.json()["data"]) == 7

    prices_response = await client.get(f"/api/data/regions/{seeded_region.id}/prices")
    assert prices_response.status_code == 200
    assert {item["crop_name"] for item in prices_response.json()["data"]} == {"Groundnut", "Paddy"}

    crops_response = await client.get(f"/api/data/regions/{seeded_region.id}/crops")
    assert crops_response.status_code == 200
    assert len(crops_response.json()["data"]) == 2

    me_response = await client.get("/api/users/me", headers=auth_headers)
    assert me_response.status_code == 200
    assert me_response.json()["data"]["region"]["region_name"] == "Cauvery Delta"

    update_response = await client.patch(
        "/api/users/me",
        json={
            "water_availability": "Moderate",
            "irrigation_type": "Drip",
            "current_crop": "Groundnut",
        },
        headers=auth_headers,
    )
    assert update_response.status_code == 200
    updated = update_response.json()["data"]
    assert updated["water_availability"] == "Moderate"
    assert updated["irrigation_type"] == "Drip"
    assert updated["current_crop"] == "Groundnut"
