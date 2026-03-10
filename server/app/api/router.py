from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import auth, chat, data, farms, health

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(chat.router)
api_router.include_router(data.router)
api_router.include_router(farms.router)

root_router = APIRouter()
root_router.include_router(api_router)
