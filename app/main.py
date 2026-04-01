from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI

from app.api.collect import router as collect_router
from app.core.redis_client import close_redis_pool, get_redis_pool


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Управление жизненным циклом приложения.
    
    Инициализация Redis пула при старте и корректное закрытие при остановке.
    """
    get_redis_pool()
    yield
    await close_redis_pool()


app = FastAPI(
    title="Analytics API",
    version="1.0.0",
    description=(
        "Внутренний API для сбора кроссплатформенных аналитических событий. "
        "Целевые показатели: 200 RPS, 3M событий/день с пакетной обработкой."
    ),
    lifespan=lifespan,
)

app.include_router(collect_router, prefix="/v1/analytics")
