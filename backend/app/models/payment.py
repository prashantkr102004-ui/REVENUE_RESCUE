from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.session import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class PaymentStatus(str, enum.Enum):
    created = "created"
    pending = "pending"
    failed = "failed"
    successful = "successful"


class Payment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "payments"
    __table_args__ = (
        UniqueConstraint("merchant_id", "external_payment_id", name="uq_payments_merchant_external_payment_id"),
        Index("ix_payments_merchant_id", "merchant_id"),
        Index("ix_payments_customer_id", "customer_id"),
        Index("ix_payments_status", "status"),
    )

    merchant_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("merchants.id"), nullable=False)
    customer_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    order_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    external_payment_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    payment_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus, name="payment_status"), nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    merchant: Mapped["Merchant"] = relationship(back_populates="payments")
    customer: Mapped["Customer"] = relationship(back_populates="payments")
    order: Mapped["Order"] = relationship(back_populates="payments")
    recovery_case: Mapped["RecoveryCase"] = relationship(back_populates="payment")
