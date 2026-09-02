"""initial database foundation

Revision ID: 202609010001
Revises:
Create Date: 2026-09-01 00:00:01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "202609010001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    payment_status = postgresql.ENUM(
        "created",
        "pending",
        "failed",
        "successful",
        name="payment_status",
        create_type=False,
    )
    recovery_case_status = postgresql.ENUM(
        "open",
        "analyzing",
        "action_pending",
        "recovering",
        "recovered",
        "failed",
        "escalated",
        name="recovery_case_status",
        create_type=False,
    )
    recovery_action_type = postgresql.ENUM(
        "retry",
        "notify",
        "offer",
        "escalate",
        name="recovery_action_type",
        create_type=False,
    )
    recovery_action_status = postgresql.ENUM(
        "proposed",
        "approved",
        "blocked",
        "executed",
        "successful",
        "failed",
        name="recovery_action_status",
        create_type=False,
    )

    bind = op.get_bind()
    payment_status.create(bind, checkfirst=True)
    recovery_case_status.create(bind, checkfirst=True)
    recovery_action_type.create(bind, checkfirst=True)
    recovery_action_status.create(bind, checkfirst=True)

    op.create_table(
        "merchants",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_merchants_created_at"), "merchants", ["created_at"], unique=False)
    op.create_index(op.f("ix_merchants_email"), "merchants", ["email"], unique=True)

    op.create_table(
        "customers",
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("external_customer_id", sa.String(length=255), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("customer_value_score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("successful_payments", sa.Integer(), server_default="0", nullable=False),
        sa.Column("failed_payments", sa.Integer(), server_default="0", nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "merchant_id",
            "external_customer_id",
            name="uq_customers_merchant_external_customer_id",
        ),
    )
    op.create_index(op.f("ix_customers_created_at"), "customers", ["created_at"], unique=False)
    op.create_index("ix_customers_merchant_id", "customers", ["merchant_id"], unique=False)

    op.create_table(
        "orders",
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("external_order_id", sa.String(length=255), nullable=True),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("merchant_id", "external_order_id", name="uq_orders_merchant_external_order_id"),
    )
    op.create_index("ix_orders_customer_id", "orders", ["customer_id"], unique=False)
    op.create_index(op.f("ix_orders_created_at"), "orders", ["created_at"], unique=False)
    op.create_index("ix_orders_merchant_id", "orders", ["merchant_id"], unique=False)

    op.create_table(
        "payments",
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("order_id", sa.Uuid(), nullable=False),
        sa.Column("external_payment_id", sa.String(length=255), nullable=True),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("payment_method", sa.String(length=50), nullable=True),
        sa.Column("status", payment_status, nullable=False),
        sa.Column("failure_reason", sa.String(length=500), nullable=True),
        sa.Column("retry_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"]),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("merchant_id", "external_payment_id", name="uq_payments_merchant_external_payment_id"),
    )
    op.create_index("ix_payments_customer_id", "payments", ["customer_id"], unique=False)
    op.create_index(op.f("ix_payments_created_at"), "payments", ["created_at"], unique=False)
    op.create_index("ix_payments_merchant_id", "payments", ["merchant_id"], unique=False)
    op.create_index("ix_payments_status", "payments", ["status"], unique=False)

    op.create_table(
        "recovery_cases",
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("payment_id", sa.Uuid(), nullable=False),
        sa.Column("status", recovery_case_status, nullable=False),
        sa.Column("revenue_at_risk", sa.Integer(), nullable=False),
        sa.Column("recovery_probability", sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column("recommended_action", sa.String(length=50), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"]),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("payment_id"),
    )
    op.create_index("ix_recovery_cases_customer_id", "recovery_cases", ["customer_id"], unique=False)
    op.create_index(op.f("ix_recovery_cases_created_at"), "recovery_cases", ["created_at"], unique=False)
    op.create_index("ix_recovery_cases_merchant_id", "recovery_cases", ["merchant_id"], unique=False)
    op.create_index("ix_recovery_cases_status", "recovery_cases", ["status"], unique=False)

    op.create_table(
        "audit_logs",
        sa.Column("merchant_id", sa.Uuid(), nullable=False),
        sa.Column("recovery_case_id", sa.Uuid(), nullable=True),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["merchant_id"], ["merchants.id"]),
        sa.ForeignKeyConstraint(["recovery_case_id"], ["recovery_cases.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_logs_created_at"), "audit_logs", ["created_at"], unique=False)
    op.create_index("ix_audit_logs_merchant_id", "audit_logs", ["merchant_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_recovery_case_id"), "audit_logs", ["recovery_case_id"], unique=False)

    op.create_table(
        "recovery_actions",
        sa.Column("recovery_case_id", sa.Uuid(), nullable=False),
        sa.Column("action_type", recovery_action_type, nullable=False),
        sa.Column("status", recovery_action_status, nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=True),
        sa.Column("retry_number", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["recovery_case_id"], ["recovery_cases.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_recovery_actions_created_at"), "recovery_actions", ["created_at"], unique=False)
    op.create_index(op.f("ix_recovery_actions_recovery_case_id"), "recovery_actions", ["recovery_case_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_recovery_actions_recovery_case_id"), table_name="recovery_actions")
    op.drop_index(op.f("ix_recovery_actions_created_at"), table_name="recovery_actions")
    op.drop_table("recovery_actions")

    op.drop_index(op.f("ix_audit_logs_recovery_case_id"), table_name="audit_logs")
    op.drop_index("ix_audit_logs_merchant_id", table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_created_at"), table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("ix_recovery_cases_status", table_name="recovery_cases")
    op.drop_index("ix_recovery_cases_merchant_id", table_name="recovery_cases")
    op.drop_index(op.f("ix_recovery_cases_created_at"), table_name="recovery_cases")
    op.drop_index("ix_recovery_cases_customer_id", table_name="recovery_cases")
    op.drop_table("recovery_cases")

    op.drop_index("ix_payments_status", table_name="payments")
    op.drop_index("ix_payments_merchant_id", table_name="payments")
    op.drop_index(op.f("ix_payments_created_at"), table_name="payments")
    op.drop_index("ix_payments_customer_id", table_name="payments")
    op.drop_table("payments")

    op.drop_index("ix_orders_merchant_id", table_name="orders")
    op.drop_index(op.f("ix_orders_created_at"), table_name="orders")
    op.drop_index("ix_orders_customer_id", table_name="orders")
    op.drop_table("orders")

    op.drop_index("ix_customers_merchant_id", table_name="customers")
    op.drop_index(op.f("ix_customers_created_at"), table_name="customers")
    op.drop_table("customers")

    op.drop_index(op.f("ix_merchants_email"), table_name="merchants")
    op.drop_index(op.f("ix_merchants_created_at"), table_name="merchants")
    op.drop_table("merchants")

    bind = op.get_bind()
    postgresql.ENUM(name="recovery_action_status").drop(bind, checkfirst=True)
    postgresql.ENUM(name="recovery_action_type").drop(bind, checkfirst=True)
    postgresql.ENUM(name="recovery_case_status").drop(bind, checkfirst=True)
    postgresql.ENUM(name="payment_status").drop(bind, checkfirst=True)
