from __future__ import annotations

import redis.asyncio as aioredis

from app.core.config import settings

_pool: aioredis.ConnectionPool | None = None


def get_redis_pool() -> aioredis.ConnectionPool:
    """
    Получить или создать пул соединений Redis.
    
    Singleton паттерн для эффективного управления соединениями.
    Максимальное количество соединений: 50.
    """
    global _pool
    if _pool is None:
        _pool = aioredis.ConnectionPool.from_url(
            settings.redis_url,
            max_connections=50,
            decode_responses=False,
        )
    return _pool


def get_redis() -> aioredis.Redis:
    """
    Получить Redis клиент с использованием пула соединений.
    
    Возвращает клиент для асинхронной работы с Redis.
    """
    return aioredis.Redis(connection_pool=get_redis_pool())


async def close_redis_pool() -> None:
    """
    Корректно закрыть все соединения Redis.
    
    Вызывается при остановке приложения для освобождения ресурсов.
    """
    global _pool
    if _pool is not None:
        await _pool.aclose()
        _pool = None
