from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import ChatMessage, ChatSession, User, utcnow
from app.services.agent_client import send_chat_request
from app.services.data_service import (
    list_latest_mandi_prices,
    list_latest_weather,
    list_region_crops,
)


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
    user = await _get_user_with_region(db, user_id)
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

    season_crops = await list_region_crops(db, user.region_id)
    weather = await list_latest_weather(db, user.region_id)
    mandi_prices = await list_latest_mandi_prices(db, user.region_id)

    payload = {
        "message": message,
        "session_history": session_history,
        "context": {
            "state": user.region.state,
            "district": user.region.district,
            "dominant_soil_type": user.region.dominant_soil_type,
            "water_availability": user.water_availability or user.region.default_water_availability,
            "irrigation_type": user.irrigation_type,
            "current_crop": user.current_crop,
            "season_crops": [
                {
                    "crop_name": crop.crop_name,
                    "crop_season": crop.crop_season,
                    "suitability_score": crop.suitability_score,
                }
                for crop in season_crops
            ],
            "weather": [
                {
                    "forecast_date": forecast.forecast_date.isoformat(),
                    "min_temp": forecast.min_temp,
                    "max_temp": forecast.max_temp,
                    "expected_rainfall_mm": forecast.expected_rainfall_mm,
                    "humidity_pct": forecast.humidity_pct,
                }
                for forecast in weather
            ],
            "mandi_prices": [
                {
                    "crop_name": price.crop_name,
                    "price_per_quintal": price.price_per_quintal,
                    "recorded_date": price.recorded_date.isoformat(),
                }
                for price in mandi_prices
            ],
        },
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
            message_metadata={"source": "agent_service"},
        )
    )
    session.updated_at = utcnow()
    await db.commit()
    await db.refresh(session)
    return session, assistant_reply
