from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.db.session import Base
from app.models.common import UUIDPrimaryKeyMixin


class WebhookEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "webhook_events"
    __table_args__ = (
        UniqueConstraint("provider", "external_event_id", name="uq_webhook_events_provider_external_event_id"),
        Index("ix_webhook_events_created_at", "created_at"),
        Index("ix_webhook_events_provider", "provider"),
    )

    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    external_event_id: Mapped[str] = mapped_column(String(255), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
