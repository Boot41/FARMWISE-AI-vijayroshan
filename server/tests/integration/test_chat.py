from __future__ import annotations

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
