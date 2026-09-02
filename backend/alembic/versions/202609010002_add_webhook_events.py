"""add webhook events

Revision ID: 202609010002
Revises: 202609010001
Create Date: 2026-09-01 00:00:02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202609010002"
down_revision: str | None = "202609010001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "webhook_events",
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("external_event_id", sa.String(length=255), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "external_event_id", name="uq_webhook_events_provider_external_event_id"),
    )
    op.create_index("ix_webhook_events_created_at", "webhook_events", ["created_at"], unique=False)
    op.create_index("ix_webhook_events_provider", "webhook_events", ["provider"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_webhook_events_provider", table_name="webhook_events")
    op.drop_index("ix_webhook_events_created_at", table_name="webhook_events")
    op.drop_table("webhook_events")
