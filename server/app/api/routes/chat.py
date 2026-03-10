from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_session
from app.middleware.auth_middleware import CurrentUser
from app.schemas.chat import ChatMessageRequest, ChatReply, ChatSessionDetail, ChatSessionSummary
from app.schemas.common import APIResponse
from app.services.chat_service import get_session_history, list_user_sessions, process_chat_message

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message", response_model=APIResponse[ChatReply])
async def create_message(
    body: ChatMessageRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(db_session),
) -> APIResponse[ChatReply]:
    session, reply = await process_chat_message(
        db,
        user_id=current_user.id,
        session_id=body.session_id,
        message=body.message,
    )
    return APIResponse(
        message="Agent response received successfully",
        data=ChatReply(session_id=session.id, session_title=session.title, reply=reply),
    )


@router.get("/sessions", response_model=APIResponse[list[ChatSessionSummary]])
async def get_sessions(
    current_user: CurrentUser,
    db: AsyncSession = Depends(db_session),
) -> APIResponse[list[ChatSessionSummary]]:
    sessions = await list_user_sessions(db, user_id=current_user.id)
    return APIResponse(
        message="Chat sessions fetched successfully",
        data=[ChatSessionSummary.model_validate(session) for session in sessions],
    )


@router.get("/sessions/{session_id}", response_model=APIResponse[ChatSessionDetail])
async def get_session_messages(
    session_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(db_session),
) -> APIResponse[ChatSessionDetail]:
    session = await get_session_history(db, session_id=session_id, user_id=current_user.id)
    return APIResponse(
        message="Chat session fetched successfully",
        data=ChatSessionDetail.model_validate(session),
    )
