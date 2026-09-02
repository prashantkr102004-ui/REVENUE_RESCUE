from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.session import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class RecoveryCaseStatus(str, enum.Enum):
    open = "open"
    analyzing = "analyzing"
    action_pending = "action_pending"
    recovering = "recovering"
    recovered = "recovered"
    failed = "failed"
    escalated = "escalated"


class RecoveryCase(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "recovery_cases"
    __table_args__ = (
        Index("ix_recovery_cases_merchant_id", "merchant_id"),
        Index("ix_recovery_cases_customer_id", "customer_id"),
        Index("ix_recovery_cases_status", "status"),
    )

    merchant_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("merchants.id"), nullable=False)
    customer_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    payment_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("payments.id"), nullable=False, unique=True)
    status: Mapped[RecoveryCaseStatus] = mapped_column(
        Enum(RecoveryCaseStatus, name="recovery_case_status"),
        nullable=False,
    )
    revenue_at_risk: Mapped[int] = mapped_column(Integer, nullable=False)
    recovery_probability: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    recommended_action: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    merchant: Mapped["Merchant"] = relationship(back_populates="recovery_cases")
    customer: Mapped["Customer"] = relationship(back_populates="recovery_cases")
    payment: Mapped["Payment"] = relationship(back_populates="recovery_case")
    actions: Mapped[list["RecoveryAction"]] = relationship(back_populates="recovery_case")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="recovery_case")
