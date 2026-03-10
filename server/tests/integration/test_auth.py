from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.db.models import Region


@pytest.mark.asyncio
async def test_register_login_refresh_logout(client: AsyncClient, seeded_region: Region) -> None:
    register_response = await client.post(
        "/api/auth/register",
        json={
            "name": "New Farmer",
            "email": "newfarmer@example.com",
            "password": "pass123",
            "phone_number": "9876543210",
            "region_id": str(seeded_region.id),
        },
    )
    assert register_response.status_code == 201
    register_body = register_response.json()
    assert register_body["success"] is True
    refresh_token = register_body["data"]["tokens"]["refresh_token"]

    login_response = await client.post(
        "/api/auth/login",
        json={"email": "newfarmer@example.com", "password": "pass123"},
    )
    assert login_response.status_code == 200
    login_body = login_response.json()
    assert login_body["data"]["user"]["email"] == "newfarmer@example.com"

    refresh_response = await client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_response.status_code == 200
    assert refresh_response.json()["data"]["token_type"] == "bearer"

    logout_response = await client.post("/api/auth/logout", json={"refresh_token": refresh_token})
    assert logout_response.status_code == 200
    assert logout_response.json()["data"]["acknowledged"] is True

    invalid_refresh = await client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert invalid_refresh.status_code == 401
