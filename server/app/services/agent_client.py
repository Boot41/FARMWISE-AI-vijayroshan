from __future__ import annotations

from typing import Any

import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings


async def send_chat_request(payload: dict[str, Any]) -> str:
    settings = get_settings()
    url = f"{settings.agent_service_url.rstrip('/')}/agent/chat"

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(url, json=payload)
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Agent service is unavailable",
            ) from exc

    if response.is_error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Agent service returned an invalid response",
        )

    try:
        body = response.json()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Agent service returned non-JSON data",
        ) from exc

    reply = body.get("reply") or body.get("response") or body.get("message")
    if reply is None and isinstance(body.get("data"), dict):
        reply = body["data"].get("reply") or body["data"].get("message")
    if not isinstance(reply, str) or not reply.strip():
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Agent service response did not contain a reply",
        )
    return reply
