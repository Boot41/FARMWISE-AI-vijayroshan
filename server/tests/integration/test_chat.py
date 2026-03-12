from __future__ import annotations

import json

import pytest
from httpx import AsyncClient

from app.db.models import User


@pytest.mark.asyncio
async def test_chat_message_creates_session_and_persists_messages(
    client: AsyncClient,
    seeded_user: User,
    auth_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_send_chat_request(payload: dict[str, object]) -> str:
        assert payload["user_id"] == str(seeded_user.id)
        assert payload["message"] == "Should I irrigate this week?"
        assert payload["session_history"] == []
        return "Irrigate lightly and watch rainfall over the next two days."

    monkeypatch.setattr("app.services.chat_service.send_chat_request", fake_send_chat_request)

    message_response = await client.post(
        "/api/chat/message",
        json={"message": "Should I irrigate this week?"},
        headers=auth_headers,
    )
    assert message_response.status_code == 200
    message_body = message_response.json()
    assert message_body["data"]["reply"].startswith("Irrigate lightly")
    session_id = message_body["data"]["session_id"]

    sessions_response = await client.get("/api/chat/sessions", headers=auth_headers)
    assert sessions_response.status_code == 200
    assert sessions_response.json()["data"][0]["id"] == session_id

    history_response = await client.get(f"/api/chat/sessions/{session_id}", headers=auth_headers)
    assert history_response.status_code == 200
    messages = history_response.json()["data"]["messages"]
    assert len(messages) == 2
    assert [message["role"] for message in messages] == ["user", "assistant"]
    assert messages[1]["message_metadata"] == {"source": "agent_service", "structured": False}


@pytest.mark.asyncio
async def test_chat_message_persists_structured_metadata_for_market_reply(
    client: AsyncClient,
    auth_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    structured_reply = json.dumps(
        {
            "intent": "market_timing",
            "crop": "Tomato",
            "current_price_per_qtl": 1450,
            "price_7d_ago": 980,
            "trend": "rising",
            "trend_pct": 48,
            "msp": None,
            "recommendation": "hold",
            "reasoning": "Price has risen 48% in 7 days.",
            "sell_by": "Within 2 weeks",
            "summary": "Hold your stock for up to 2 more weeks.",
        }
    )

    async def fake_send_chat_request(payload: dict[str, object]) -> str:
        assert payload["message"] == "Should I sell my tomatoes now?"
        return structured_reply

    monkeypatch.setattr("app.services.chat_service.send_chat_request", fake_send_chat_request)

    response = await client.post(
        "/api/chat/message",
        json={"message": "Should I sell my tomatoes now?"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    session_id = response.json()["data"]["session_id"]

    history_response = await client.get(f"/api/chat/sessions/{session_id}", headers=auth_headers)
    assert history_response.status_code == 200
    messages = history_response.json()["data"]["messages"]
    assistant = messages[1]

    assert assistant["message_text"] == structured_reply
    assert assistant["message_metadata"] == {
        "source": "agent_service",
        "structured": True,
        "intent": "market_timing",
        "data": {
            "crop": "Tomato",
            "current_price": 1450,
            "price_unit": "qtl",
            "trend": "rising",
            "trend_pct": 48,
            "advice": "Price has risen 48% in 7 days. Hold your stock for up to 2 more weeks.",
        },
    }
