from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.session import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class Customer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "customers"
    __table_args__ = (
        UniqueConstraint("merchant_id", "external_customer_id", name="uq_customers_merchant_external_customer_id"),
        Index("ix_customers_merchant_id", "merchant_id"),
    )

    merchant_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("merchants.id"), nullable=False)
    external_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    customer_value_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    successful_payments: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    failed_payments: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    merchant: Mapped["Merchant"] = relationship(back_populates="customers")
    orders: Mapped[list["Order"]] = relationship(back_populates="customer")
    payments: Mapped[list["Payment"]] = relationship(back_populates="customer")
    recovery_cases: Mapped[list["RecoveryCase"]] = relationship(back_populates="customer")
