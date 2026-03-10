from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "OK"
    data: T


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    data: None = None
    errors: list[dict[str, object]] | None = None


class MessageAck(BaseModel):
    model_config = ConfigDict(extra="forbid")

    acknowledged: bool = True
    detail: str | None = None


class EmptyPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    placeholder: str = Field(default="ok")
