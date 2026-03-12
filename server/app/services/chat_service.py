from __future__ import annotations

import json
import re
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import ChatMessage, ChatSession, User, utcnow
from app.services.agent_client import send_chat_request

KNOWN_INTENTS = {
    "crop_recommendation",
    "pest_diagnosis",
    "irrigation_schedule",
    "market_timing",
}


def _compact_text(parts: list[str | None]) -> str | None:
    values = [part.strip() for part in parts if isinstance(part, str) and part.strip()]
    if not values:
        return None
    return " ".join(values)


def _extract_expected_rainfall(reason: str | None) -> float | None:
    if not reason:
        return None
    match = re.search(r"(\d+(?:\.\d+)?)\s*mm", reason, flags=re.IGNORECASE)
    if match is None:
        return None
    return float(match.group(1))


def _normalize_crop_recommendation(parsed: dict[str, object]) -> dict[str, object]:
    crops = parsed.get("crops")
    if not isinstance(crops, list) or not crops:
        return {}
    first_crop = crops[0]
    if not isinstance(first_crop, dict):
        return {}
    summary = parsed.get("summary")
    summary_text = summary if isinstance(summary, str) else None
    why_recommended = first_crop.get("why_recommended")
    why_recommended_text = why_recommended if isinstance(why_recommended, str) else None
    scheme = first_crop.get("scheme")
    scheme_text = scheme if isinstance(scheme, str) else None

    return {
        "crop": first_crop.get("name"),
        "season": None,
        "sowing_window": first_crop.get("sowing_window"),
        "harvest_window": first_crop.get("harvest_window"),
        "water_requirement": first_crop.get("water_requirement"),
        "estimated_cost": first_crop.get("estimated_cost_per_ha"),
        "expected_yield": first_crop.get("expected_yield_qtl_per_ha"),
        "expected_revenue": first_crop.get("expected_revenue_per_ha"),
        "notes": _compact_text(
            [
                why_recommended_text,
                scheme_text,
                summary_text,
            ]
        ),
    }


def _normalize_pest_diagnosis(parsed: dict[str, object]) -> dict[str, object]:
    treatment = parsed.get("treatment")
    treatment_data = treatment if isinstance(treatment, dict) else {}
    symptoms = parsed.get("symptoms_matched")
    symptom_text = (
        ", ".join(item for item in symptoms if isinstance(item, str))
        if isinstance(symptoms, list)
        else None
    )

    return {
        "pest_name": parsed.get("diagnosis"),
        "crop": parsed.get("crop"),
        "symptoms": symptom_text,
        "treatment": treatment_data.get("chemical"),
        "dosage": treatment_data.get("dosage"),
        "frequency": treatment_data.get("frequency"),
        "organic_alternative": treatment_data.get("organic"),
        "warning": parsed.get("spray_warning"),
    }


def _normalize_market_timing(parsed: dict[str, object]) -> dict[str, object]:
    reasoning = parsed.get("reasoning")
    reasoning_text = reasoning if isinstance(reasoning, str) else None
    summary = parsed.get("summary")
    summary_text = summary if isinstance(summary, str) else None

    return {
        "crop": parsed.get("crop"),
        "current_price": parsed.get("current_price_per_qtl"),
        "price_unit": "qtl",
        "trend": parsed.get("trend"),
        "trend_pct": parsed.get("trend_pct"),
        "advice": _compact_text([reasoning_text, summary_text]),
    }


def _normalize_irrigation_schedule(parsed: dict[str, object]) -> dict[str, object]:
    schedule = parsed.get("schedule")
    summary = parsed.get("summary")
    summary_text = summary if isinstance(summary, str) else None
    entries = (
        [item for item in schedule if isinstance(item, dict)] if isinstance(schedule, list) else []
    )
    first_irrigate = next(
        (
            entry
            for entry in entries
            if entry.get("action") == "irrigate" and isinstance(entry.get("date"), str)
        ),
        None,
    )
    skip_entries = [
        entry
        for entry in entries
        if entry.get("action") == "skip" and isinstance(entry.get("date"), str)
    ]
    first_skip = skip_entries[0] if skip_entries else None
    first_irrigate_reason = (
        first_irrigate.get("reason")
        if first_irrigate and isinstance(first_irrigate.get("reason"), str)
        else None
    )
    first_skip_reason = (
        first_skip.get("reason")
        if first_skip and isinstance(first_skip.get("reason"), str)
        else None
    )

    return {
        "next_watering_date": first_irrigate.get("date") if first_irrigate else None,
        "skip_dates": [entry["date"] for entry in skip_entries],
        "expected_rainfall_mm": _extract_expected_rainfall(first_skip_reason),
        "rainfall_date": first_skip.get("date") if first_skip else None,
        "reason": _compact_text([summary_text, first_irrigate_reason, first_skip_reason]),
    }


def _normalize_structured_data(intent: str, parsed: dict[str, object]) -> dict[str, object]:
    if intent == "crop_recommendation":
        return _normalize_crop_recommendation(parsed)
    if intent == "pest_diagnosis":
        return _normalize_pest_diagnosis(parsed)
    if intent == "market_timing":
        return _normalize_market_timing(parsed)
    if intent == "irrigation_schedule":
        return _normalize_irrigation_schedule(parsed)
    return {}


def _detect_metadata(reply: str) -> dict[str, object]:
    try:
        parsed = json.loads(reply)
    except ValueError:
        return {"source": "agent_service", "structured": False}

    if not isinstance(parsed, dict):
        return {"source": "agent_service", "structured": False}

    intent = parsed.get("intent")
    if not isinstance(intent, str) or intent not in KNOWN_INTENTS:
        return {"source": "agent_service", "structured": False}

    return {
        "source": "agent_service",
        "structured": True,
        "intent": intent,
        "data": _normalize_structured_data(intent, parsed),
    }


def _build_session_title(message: str) -> str:
    compact = " ".join(message.split())
    return compact[:60] if len(compact) <= 60 else f"{compact[:57]}..."


async def _get_user_with_region(db: AsyncSession, user_id: UUID) -> User:
    result = await db.execute(
        select(User).options(selectinload(User.region)).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


async def _get_session_for_user(db: AsyncSession, session_id: UUID, user_id: UUID) -> ChatSession:
    result = await db.execute(
        select(ChatSession)
        .options(selectinload(ChatSession.messages))
        .where(ChatSession.id == session_id, ChatSession.user_id == user_id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
    return session


async def list_user_sessions(db: AsyncSession, *, user_id: UUID) -> list[ChatSession]:
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .order_by(desc(ChatSession.updated_at), desc(ChatSession.created_at))
    )
    return list(result.scalars().all())


async def get_session_history(db: AsyncSession, *, session_id: UUID, user_id: UUID) -> ChatSession:
    return await _get_session_for_user(db, session_id, user_id)


async def process_chat_message(
    db: AsyncSession,
    *,
    user_id: UUID,
    session_id: UUID | None,
    message: str,
) -> tuple[ChatSession, str]:
    await _get_user_with_region(db, user_id)
    if session_id is None:
        session = ChatSession(user_id=user_id, title=_build_session_title(message))
        db.add(session)
        await db.flush()
        session_history: list[dict[str, str]] = []
    else:
        session = await _get_session_for_user(db, session_id, user_id)
        session_history = [
            {"role": msg.role, "message_text": msg.message_text}
            for msg in sorted(session.messages, key=lambda item: item.created_at)
        ]

    payload = {
        "user_id": str(user_id),
        "message": message,
        "session_history": session_history,
    }
    assistant_reply = await send_chat_request(payload)

    db.add(
        ChatMessage(
            session_id=session.id,
            role="user",
            message_text=message,
            message_metadata={"source": "client"},
        )
    )
    db.add(
        ChatMessage(
            session_id=session.id,
            role="assistant",
            message_text=assistant_reply,
            message_metadata=_detect_metadata(assistant_reply),
        )
    )
    session.updated_at = utcnow()
    await db.commit()
    await db.refresh(session)
    return session, assistant_reply
