from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader

from app.core.config import settings
from app.core.redis_client import get_redis

router = APIRouter()

_server_api_key_header = APIKeyHeader(name="X-Analytics-Server-Token", auto_error=False)


def _serialize_events(events: list[Dict[str, Any]], source: str) -> list[bytes]:
    """Сериализация событий для Redis очереди."""
    result: list[bytes] = []
    for ev in events:
        payload = ev.copy()
        payload["_source"] = source
        payload.setdefault("server_time", datetime.now(tz=timezone.utc).isoformat())
        result.append(json.dumps(payload, ensure_ascii=False).encode())
    return result


async def _push_to_redis(
    redis: aioredis.Redis,
    payloads: list[bytes],
) -> None:
    """Отправка событий в Redis очередь."""
    if not payloads:
        return
    await redis.rpush(settings.redis_events_queue, *payloads)  # type: ignore[arg-type]


@router.post(
    "/frontend/collect",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Accept frontend events batch",
    tags=["Frontend Events"],
)
async def frontend_collect(
    events: list[Dict[str, Any]],
    redis: aioredis.Redis = Depends(get_redis),
) -> dict[str, int]:
    """
    Принимает пакет событий от frontend.
    
    Пример архитектуры API для сбора аналитических событий.
    Реальная схема валидации зависит от требований проекта.
    """
    if not events:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty batch.")
    
    # В реальном проекте здесь валидация событий по схеме
    payloads = _serialize_events(events, source="frontend")
    await _push_to_redis(redis, payloads)
    return {"accepted": len(payloads)}


async def _verify_server_token(
    api_key: str | None = Security(_server_api_key_header),
) -> str:
    """Верификация серверного токена."""
    if api_key != settings.server_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Analytics-Server-Token.",
        )
    return api_key


@router.post(
    "/backend/collect",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Accept backend events batch (server-to-server)",
    tags=["Backend Events"],
)
async def backend_collect(
    events: list[Dict[str, Any]],
    _token: str = Depends(_verify_server_token),
    redis: aioredis.Redis = Depends(get_redis),
) -> dict[str, int]:
    """
    Принимает пакет событий от backend сервисов.
    
    Пример server-to-server API для сбора событий.
    Использует API key аутентификацию.
    """
    if not events:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty batch.")
    
    # В реальном проекте здесь валидация событий по схеме
    payloads = _serialize_events(events, source="backend")
    await _push_to_redis(redis, payloads)
    return {"accepted": len(payloads)}
