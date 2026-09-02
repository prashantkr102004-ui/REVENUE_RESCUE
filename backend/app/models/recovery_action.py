from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.session import Base
from app.models.common import UUIDPrimaryKeyMixin


class RecoveryActionType(str, enum.Enum):
    retry = "retry"
    notify = "notify"
    offer = "offer"
    escalate = "escalate"


class RecoveryActionStatus(str, enum.Enum):
    proposed = "proposed"
    approved = "approved"
    blocked = "blocked"
    executed = "executed"
    successful = "successful"
    failed = "failed"


class RecoveryAction(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "recovery_actions"
    __table_args__ = (Index("ix_recovery_actions_created_at", "created_at"),)

    recovery_case_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("recovery_cases.id"),
        nullable=False,
        index=True,
    )
    action_type: Mapped[RecoveryActionType] = mapped_column(
        Enum(RecoveryActionType, name="recovery_action_type"),
        nullable=False,
    )
    status: Mapped[RecoveryActionStatus] = mapped_column(
        Enum(RecoveryActionStatus, name="recovery_action_status"),
        nullable=False,
    )
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    retry_number: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    recovery_case: Mapped["RecoveryCase"] = relationship(back_populates="actions")
