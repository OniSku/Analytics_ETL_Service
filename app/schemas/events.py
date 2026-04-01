from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class BaseEvent(BaseModel):
    """
    Базовая структура события для аналитической системы.
    
    Пример архитектуры - реальная структура зависит от требований проекта.
    """
    event_id: uuid.UUID = Field(description="Unique event ID for deduplication.")
    session_id: Optional[str] = Field(default=None, description="Session identifier.")
    user_id: Optional[uuid.UUID] = Field(
        default=None,
        description="Registered user ID. May be null.",
    )
    client_id: Optional[uuid.UUID] = Field(default=None, description="Device/browser identifier.")
    url: str = Field(description="Event page URL.")
    event_name: str = Field(description="Event name from catalog.")
    event_params: dict[str, Any] = Field(
        default_factory=dict,
        description="Event parameters (flexible container).",
    )
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Technical metadata (User-Agent, IP, version).",
    )


class FrontendContext(BaseModel):
    """Контекст для frontend событий."""
    user_agent: str | None = None
    screen_resolution: str | None = None
    referrer_url: str | None = None


# Примеры типов событий - в реальном проекте определяются бизнес-требованиями
FrontendEventName = Literal[
    "page_viewed",
    "action_completed",
    "feature_used",
    "error_occurred",
]

BackendEventName = Literal[
    "user_registered",
    "user_logged_in",
    "process_started",
    "process_completed",
    "payment_processed",
    "subscription_changed",
]


class FrontendEvent(BaseEvent):
    """Событие от frontend клиента."""
    event_name: FrontendEventName
    context: FrontendContext | dict[str, Any] = Field(default_factory=dict)


class BackendEvent(BaseEvent):
    """Событие от backend сервиса."""
    event_name: BackendEventName
    server_time: datetime = Field(
        description="Server-side event timestamp.",
    )


# Примеры параметров событий - в реальном проекте определяются бизнес-логикой
class ProcessParams(BaseModel):
    """Параметры процессных событий."""
    process_id: str = Field(description="Process identifier.")
    duration_ms: int = Field(ge=0, description="Duration in milliseconds.")
    status: str = Field(description="Process status.")
    
    # Пример валидации
    # def validate_status(cls, v: str) -> str:
    #     allowed = {"success", "failed", "timeout", "cancelled"}
    #     if v not in allowed:
    #         raise ValueError(f"status must be one of {allowed}")
    #     return v


class PaymentParams(BaseModel):
    """Параметры платежных событий."""
    payment_id: str = Field(description="Payment identifier.")
    amount: float = Field(ge=0, description="Payment amount.")
    currency: str = Field(description="Currency code.")
    
    # Пример валидации
    # def validate_currency(cls, v: str) -> str:
    #     if len(v) != 3:
    #         raise ValueError("Currency must be 3-letter code")
    #     return v.upper()
