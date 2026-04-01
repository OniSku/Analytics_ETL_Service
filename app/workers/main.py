import asyncio
import os
import threading

from celery import Celery

from app.workers.etl_worker import ETLWorker

celery_app = Celery(
    "analytics_tasks",
    broker=f"redis://{os.environ['REDIS_HOST']}:{os.environ['REDIS_PORT']}/{os.environ['REDIS_DB']}",
    backend=f"redis://{os.environ['REDIS_HOST']}:{os.environ['REDIS_PORT']}/{os.environ['REDIS_DB']}",
)


@celery_app.task
def ping() -> str:
    """
    Проверка работоспособности Celery воркера.
    
    Returns:
        str: "pong" для подтверждения работы
    """
    return "pong"


def _run_etl_loop() -> None:
    """
    Запуск ETL воркера в отдельном потоке.
    
    Создает новый event loop для асинхронной работы,
    запускает ETL процесс для обработки событий.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    worker = ETLWorker()
    loop.run_until_complete(worker.start())


etl_thread = threading.Thread(target=_run_etl_loop, daemon=True)
etl_thread.start()
