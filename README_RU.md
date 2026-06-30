# Analytics ETL Service

> ⚠️ **Дисклеймер**: Этот репозиторий является витриной кода (showcase) для демонстрации. Он не содержит полноценной рабочей среды и всех проприетарных зависимостей.

Микросервис сбора и обработки кросс-платформенных аналитических событий. Сервис принимает пакеты событий от фронтенда и бэкенда, буферизует их в Redis и асинхронно записывает в PostgreSQL Data Warehouse с размерной моделью (звезда-схема).

Целевые показатели производительности: **200 RPS**, **3 миллиона событий в день** с пакетной обработкой.

---

## Стек технологий

| Слой | Технология |
|---|---|
| Язык | Python 3.10+ |
| API-фреймворк | FastAPI 0.115 |
| Очередь задач | Celery 5.4 |
| Брокер / буфер сообщений | Redis 7 |
| ORM | SQLAlchemy 2.0 (async) |
| База данных | PostgreSQL 15 |
| Драйвер БД | asyncpg |
| Миграции | Alembic |
| Валидация | Pydantic v2 / pydantic-settings |
| Сервер | Uvicorn |
| Контейнеризация | Docker / Docker Compose |

---

## Архитектура

```
Frontend / Backend сервисы
        |
        v
  FastAPI (collect.py)
        |
  [HTTP 202 Accepted]
        |
        v
   Redis-очередь
 (analytics:events:queue)
        |
        v
  Celery ETL Worker
  (etl_worker.py)
        |
        +---> EventDispatcher (dispatcher.py)
        |           |
        |    Маршрутизация по event_name:
        |    - user_registered  --> dim_entities (upsert)
        |    - payment_processed / subscription_changed --> fact_metrics + dim_entities (update)
        |
        v
   PostgreSQL DWH
   ├── dim_entities    (измерение: пользователи / сущности)
   ├── fact_events     (лог событий, дедупликация по event_id)
   └── fact_metrics    (финансовые / числовые метрики)
```

**Описание потока данных:**
1. API-эндпоинты принимают JSON-пакеты событий и записывают сериализованные данные в Redis-список одним вызовом `RPUSH`.
2. ETL Worker опрашивает Redis каждые 2 секунды и извлекает до `REDIS_BATCH_SIZE` (по умолчанию 500) событий за цикл.
3. События массово вставляются в `fact_events` с использованием PostgreSQL `ON CONFLICT DO NOTHING` для дедупликации.
4. `EventDispatcher` маршрутизирует конкретные бизнес-события для обновления размерных таблиц.

---

## Структура проекта

```
analytics_etl_showcase/
├── app/
│   ├── api/
│   │   └── collect.py          # POST /v1/analytics/frontend|backend/collect
│   ├── core/
│   │   ├── config.py           # Настройки через pydantic-settings (.env)
│   │   └── redis_client.py     # Асинхронный пул подключений к Redis
│   ├── db/
│   │   ├── base.py             # Async-движок и фабрика сессий SQLAlchemy
│   │   └── models.py           # ORM-модели: DimEntity, FactEvent, FactMetric
│   ├── schemas/
│   │   └── events.py           # Pydantic-схемы для валидации событий
│   ├── workers/
│   │   ├── etl_worker.py       # ETLWorker: цикл пакетной обработки
│   │   ├── dispatcher.py       # EventDispatcher: маршрутизация бизнес-событий
│   │   └── main.py             # Точка входа Celery-приложения
│   └── main.py                 # Фабрика FastAPI-приложения
├── .env.example                # Шаблон переменных окружения
├── docker-compose.yml          # Оркестрация: api, celery_worker, postgres, redis
├── Dockerfile
└── requirements.txt
```

---

## Ключевые возможности

- **Раздельные эндпоинты сбора** — отдельные маршруты для событий фронтенда (без аутентификации) и бэкенда (API-ключ через заголовок `X-Analytics-Server-Token`).
- **Буферизация через Redis** — события записываются в Redis-список немедленно; API возвращает HTTP 202 без ожидания операций с базой данных.
- **Пакетная вставка** — ETL Worker опрашивает очередь пакетами настраиваемого размера (по умолчанию 500) и использует массовую вставку PostgreSQL для высокой пропускной способности.
- **Дедупликация** — `ON CONFLICT DO NOTHING` по `event_id` предотвращает дублирование записей при повторных запросах.
- **Event Dispatcher** — маршрутизирует именованные бизнес-события (`user_registered`, `payment_processed`, `subscription_changed`) для обновления размерных таблиц независимо от лога событий.
- **Звезда-схема DWH** — таблицы `dim_*` хранят состояние сущностей; таблицы `fact_*` хранят неизменяемые записи событий и метрик с JSONB-полями для гибкости схемы.
- **Полностью асинхронный** — FastAPI + asyncpg + async redis-py обеспечивают неблокирующий ввод/вывод на всех уровнях.
- **Docker Compose с healthcheck** — сервисы `postgres` и `redis` имеют проверки здоровья; `api` и `celery_worker` ждут готовности зависимостей перед запуском.

---

## Установка и запуск

### Требования

- Docker и Docker Compose

### 1. Клонирование и настройка окружения

```bash
git clone https://github.com/OniSku/Analytics_ETL_Service.git
cd Analytics_ETL_Service
cp .env.example .env
```

Отредактируйте `.env` и заполните значения:

| Переменная | По умолчанию | Описание |
|---|---|---|
| `POSTGRES_USER` | `analytics` | Имя пользователя PostgreSQL |
| `POSTGRES_PASSWORD` | — | Пароль PostgreSQL (обязательно) |
| `POSTGRES_DB` | `analytics_dwh` | Имя базы данных |
| `POSTGRES_HOST` | `postgres` | Хост (имя сервиса внутри Docker) |
| `POSTGRES_PORT` | `5432` | Порт PostgreSQL |
| `REDIS_HOST` | `redis` | Хост Redis |
| `REDIS_PORT` | `6379` | Порт Redis |
| `REDIS_DB` | `0` | Индекс базы данных Redis |
| `SERVER_API_KEY` | — | Секретный токен для `X-Analytics-Server-Token` (обязательно) |
| `REDIS_EVENTS_QUEUE` | `analytics:events:raw` | Ключ Redis-списка для очереди событий |
| `REDIS_BATCH_SIZE` | `500` | Количество событий за один цикл воркера |

### 2. Запуск всех сервисов

```bash
docker compose up -d --build
```

Запускает четыре контейнера: `postgres`, `redis`, `api`, `celery_worker`.

### 3. Создание таблиц базы данных

```bash
docker compose exec api python -c "
import asyncio
from app.db.base import engine
from app.db.models import Base
asyncio.run(engine.begin().__aenter__().run_sync(Base.metadata.create_all))
"
```

Или через Alembic-миграции (при наличии сгенерированных ревизий):

```bash
docker compose exec api alembic upgrade head
```

### 4. Проверка работоспособности

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health check: `GET http://localhost:8000/`

---

## API-эндпоинты

| Метод | Путь | Аутентификация | Описание |
|---|---|---|---|
| `POST` | `/v1/analytics/frontend/collect` | Нет | Принять JSON-массив событий фронтенда |
| `POST` | `/v1/analytics/backend/collect` | Заголовок `X-Analytics-Server-Token` | Принять JSON-массив серверных событий |

**Тело запроса** (оба эндпоинта): JSON-массив объектов событий. Поля `_source` и `server_time` добавляются автоматически.

```json
[
  {
    "event_name": "page_view",
    "user_id": "abc123",
    "page": "/home"
  }
]
```

**Ответ** (HTTP 202):

```json
{ "accepted": 1 }
```

---

## Примечания о статусе showcase

Репозиторий демонстрирует архитектурные паттерны для высоконагруженного конвейера приема аналитики:

- Методы `ETLWorker.process_batch()` и `EventDispatcher._handle_*` содержат задокументированные заглушки — реальная SQL-логика (массовые upsert, обновление измерений) зависит от конкретной DWH-схемы производственного проекта и не включена в репозиторий.
- Слой валидации `schemas/events.py` намеренно минимален; реальное развертывание требует строгих схем событий для каждого источника.
- Тестовый набор не включен в данный showcase.
