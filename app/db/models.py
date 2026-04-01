from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    DECIMAL,
    UUID,
    Boolean,
    ForeignKey,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import TIMESTAMP as TIMESTAMPTZ
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# Пример архитектуры аналитической системы
# Реальная структура данных зависит от требований проекта

class DimEntity(Base):
    """Пример измерения (dimension) для аналитики."""
    __tablename__ = "dim_entities"

    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    created_at: Mapped[str] = mapped_column(
        TIMESTAMPTZ,
        nullable=False,
    )
    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    properties: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        default=dict,
    )


class FactEvent(Base):
    """Пример таблицы фактов (fact table) для событий."""
    __tablename__ = "fact_events"

    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        default=uuid.uuid4,
    )
    event_time: Mapped[str] = mapped_column(
        TIMESTAMPTZ,
        nullable=False,
    )
    entity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dim_entities.entity_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    event_data: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        default=dict,
    )
    metadata: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        default=dict,
    )

    entity: Mapped[DimEntity | None] = relationship(
        "DimEntity",
        lazy="raise",
    )


class FactMetric(Base):
    """Пример таблицы для метрик и транзакций."""
    __tablename__ = "fact_metrics"

    metric_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    metric_time: Mapped[str] = mapped_column(
        TIMESTAMPTZ,
        nullable=False,
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dim_entities.entity_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    metric_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    value: Mapped[Decimal] = mapped_column(
        DECIMAL(15, 2),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )
    attributes: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        default=dict,
    )

    entity: Mapped[DimEntity] = relationship(
        "DimEntity",
        lazy="raise",
    )
