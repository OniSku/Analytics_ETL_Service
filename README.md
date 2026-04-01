# Analytics ETL Service

Сервис сбора и обработки аналитических событий. Принимает события с фронтенда и бэкенда, буферизует через Redis и записывает в PostgreSQL DWH.

## Стек

Python 3.10, FastAPI, Redis, Celery, SQLAlchemy 2.0, PostgreSQL 15, Docker

## Архитектура

Frontend/Backend → FastAPI → Redis → Celery Worker → PostgreSQL
                                                ↓
                                        Event Dispatcher
                                                ↓
                                   dim_* / fact_* таблицы

## Возможности

- Батчевый прием событий
- Bulk insert пачками по 500 записей
- Event Dispatcher - обновление аналитических измерений при бизнес-событиях
- Дедупликация по event_id
- Раздельные эндпоинты для фронтенда и бэкенда

## Быстрый старт

1. Скопировать ".env.example" в ".env" и заполнить значения
2. "docker compose up -d --build"
3. Создать таблицы: "docker compose exec api python -c "from app.db.base import engine; from app.db.models import Base; import asyncio; asyncio.run(engine.begin().__aenter__().run_sync(Base.metadata.create_all))""
4. Swagger UI: "http://localhost/docs"

## Эндпоинты

- "POST /v1/analytics/frontend/collect" - события фронтенда
- "POST /v1/analytics/backend/collect" - серверные события (заголовок "X-Analytics-Server-Token")
