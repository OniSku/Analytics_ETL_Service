# Analytics ETL Service

> ⚠️ **Disclaimer**: This repository serves as a code showcase for demonstration purposes. It does not contain a fully runnable production environment or all proprietary backend dependencies.

A microservice for collecting and processing cross-platform analytics events. The service accepts event batches from frontend and backend sources, buffers them in Redis, and asynchronously bulk-inserts them into a PostgreSQL Data Warehouse structured around a dimensional (star-schema) model.

Design targets: **200 RPS**, **3 million events per day** with batch processing.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| API Framework | FastAPI 0.115 |
| Task Queue | Celery 5.4 |
| Message Broker / Buffer | Redis 7 |
| ORM | SQLAlchemy 2.0 (async) |
| Database | PostgreSQL 15 |
| Database Driver | asyncpg |
| Migrations | Alembic |
| Validation | Pydantic v2 / pydantic-settings |
| Runtime | Uvicorn |
| Containerization | Docker / Docker Compose |

---

## Architecture

```
Frontend / Backend Services
        |
        v
  FastAPI (collect.py)
        |
  [HTTP 202 Accepted]
        |
        v
   Redis Queue
 (analytics:events:queue)
        |
        v
  Celery ETL Worker
  (etl_worker.py)
        |
        +---> EventDispatcher (dispatcher.py)
        |           |
        |    Routes by event_name:
        |    - user_registered  --> dim_entities (upsert)
        |    - payment_processed / subscription_changed --> fact_metrics + dim_entities (update)
        |
        v
   PostgreSQL DWH
   ├── dim_entities    (dimension: users / entities)
   ├── fact_events     (raw event log, dedup by event_id)
   └── fact_metrics    (financial / numeric metrics)
```

**Flow summary:**
1. API endpoints accept JSON event batches and push serialized payloads to a Redis list in a single `RPUSH` call.
2. The ETL Worker polls Redis every 2 seconds and drains up to `REDIS_BATCH_SIZE` (default 500) events per cycle.
3. Events are bulk-inserted into `fact_events` using PostgreSQL `ON CONFLICT DO NOTHING` for deduplication.
4. The `EventDispatcher` routes specific business events to update dimensional tables.

---

## Project Structure

```
analytics_etl_showcase/
├── app/
│   ├── api/
│   │   └── collect.py          # POST /v1/analytics/frontend|backend/collect
│   ├── core/
│   │   ├── config.py           # Settings via pydantic-settings (.env)
│   │   └── redis_client.py     # Async Redis connection pool
│   ├── db/
│   │   ├── base.py             # SQLAlchemy async engine & session factory
│   │   └── models.py           # ORM models: DimEntity, FactEvent, FactMetric
│   ├── schemas/
│   │   └── events.py           # Pydantic schemas for event validation
│   ├── workers/
│   │   ├── etl_worker.py       # ETLWorker: batch drain loop
│   │   ├── dispatcher.py       # EventDispatcher: business-event routing
│   │   └── main.py             # Celery application entry point
│   └── main.py                 # FastAPI application factory
├── .env.example                # Environment variable template
├── docker-compose.yml          # Orchestrates api, celery_worker, postgres, redis
├── Dockerfile
└── requirements.txt
```

---

## Key Features

- **Separate collection endpoints** — distinct routes for frontend events (unauthenticated) and backend server-to-server events (API key via `X-Analytics-Server-Token` header).
- **Redis buffering** — events are written to a Redis list immediately; the API returns HTTP 202 without waiting for database I/O.
- **Batch bulk-insert** — the ETL worker drains the queue in configurable batches (default 500) and uses PostgreSQL bulk insert for high throughput.
- **Deduplication** — `ON CONFLICT DO NOTHING` on `event_id` prevents duplicate records on retry.
- **Event Dispatcher** — routes named business events (`user_registered`, `payment_processed`, `subscription_changed`) to update dimensional tables independently of the raw event log.
- **Star-schema DWH** — `dim_*` tables hold entity state; `fact_*` tables hold immutable event and metric records with JSONB payloads for schema flexibility.
- **Async throughout** — FastAPI + asyncpg + redis-py async ensure non-blocking I/O end-to-end.
- **Health-checked Docker Compose** — `postgres` and `redis` services use healthchecks; `api` and `celery_worker` wait for dependencies before starting.

---

## Installation & Setup

### Prerequisites

- Docker and Docker Compose

### 1. Clone and configure environment

```bash
git clone https://github.com/OniSku/Analytics_ETL_Service.git
cd Analytics_ETL_Service
cp .env.example .env
```

Edit `.env` and fill in your values:

| Variable | Default | Description |
|---|---|---|
| `POSTGRES_USER` | `analytics` | PostgreSQL username |
| `POSTGRES_PASSWORD` | — | PostgreSQL password (required) |
| `POSTGRES_DB` | `analytics_dwh` | Database name |
| `POSTGRES_HOST` | `postgres` | Hostname (use service name inside Docker) |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
| `REDIS_HOST` | `redis` | Redis hostname |
| `REDIS_PORT` | `6379` | Redis port |
| `REDIS_DB` | `0` | Redis database index |
| `SERVER_API_KEY` | — | Secret token for `X-Analytics-Server-Token` (required) |
| `REDIS_EVENTS_QUEUE` | `analytics:events:raw` | Redis list key for the event queue |
| `REDIS_BATCH_SIZE` | `500` | Events drained per worker cycle |

### 2. Start all services

```bash
docker compose up -d --build
```

This starts four containers: `postgres`, `redis`, `api`, `celery_worker`.

### 3. Create database tables

```bash
docker compose exec api python -c "
import asyncio
from app.db.base import engine
from app.db.models import Base
asyncio.run(engine.begin().__aenter__().run_sync(Base.metadata.create_all))
"
```

Or use Alembic migrations if you have generated revision files:

```bash
docker compose exec api alembic upgrade head
```

### 4. Verify

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health check: `GET http://localhost:8000/` (FastAPI root)

---

## API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/v1/analytics/frontend/collect` | None | Accept a JSON array of frontend events |
| `POST` | `/v1/analytics/backend/collect` | `X-Analytics-Server-Token` header | Accept a JSON array of backend (server-to-server) events |

**Request body** (both endpoints): a JSON array of event objects. Each object may contain any fields; `_source` and `server_time` are injected automatically.

```json
[
  {
    "event_name": "page_view",
    "user_id": "abc123",
    "page": "/home"
  }
]
```

**Response** (HTTP 202):

```json
{ "accepted": 1 }
```

---

## Notes on Showcase Status

This repository demonstrates architectural patterns for a high-throughput analytics ingestion pipeline:

- The `ETLWorker.process_batch()` and `EventDispatcher._handle_*` methods contain documented stubs — actual SQL logic (bulk upserts, dimension updates) depends on the specific DWH schema of the production project and is not included.
- The `schemas/events.py` validation layer is intentionally minimal; a real deployment would enforce strict event schemas per source.
- No test suite is included in this showcase.
