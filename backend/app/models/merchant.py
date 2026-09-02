from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class Merchant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "merchants"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)

    customers: Mapped[list["Customer"]] = relationship(back_populates="merchant")
    orders: Mapped[list["Order"]] = relationship(back_populates="merchant")
    payments: Mapped[list["Payment"]] = relationship(back_populates="merchant")
    recovery_cases: Mapped[list["RecoveryCase"]] = relationship(back_populates="merchant")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="merchant")
