import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.recovery_case import RecoveryCaseStatus


class RecoveryCaseRead(BaseModel):
    id: uuid.UUID
    merchant_id: uuid.UUID
    customer_id: uuid.UUID
    payment_id: uuid.UUID
    status: RecoveryCaseStatus
    revenue_at_risk: int
    recovery_probability: Decimal | None
    recommended_action: str | None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
