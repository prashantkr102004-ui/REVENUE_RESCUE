from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.order import Order
from app.models.payment import Payment, PaymentStatus
from app.models.webhook_event import WebhookEvent
from app.services.razorpay_service import RazorpayService, RazorpaySignatureError, stable_event_id

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def get_razorpay_service() -> RazorpayService:
    return RazorpayService(get_settings())


@router.post("/razorpay")
async def handle_razorpay_webhook(
    request: Request,
    x_razorpay_signature: str | None = Header(default=None),
    db: Session = Depends(get_db),
    razorpay_service: RazorpayService = Depends(get_razorpay_service),
) -> dict[str, str]:
    raw_body = await request.body()
    try:
        razorpay_service.verify_webhook_signature(raw_body=raw_body, signature=x_razorpay_signature)
    except RazorpaySignatureError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        payload: dict[str, Any] = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid webhook JSON payload") from exc

    event_type = payload.get("event")
    if not isinstance(event_type, str):
        raise HTTPException(status_code=400, detail="Webhook event type is missing")

    external_event_id = stable_event_id(payload, raw_body)
    existing_event = db.scalar(
        select(WebhookEvent).where(
            WebhookEvent.provider == "razorpay",
            WebhookEvent.external_event_id == external_event_id,
        )
    )
    if existing_event and existing_event.processed_at is not None:
        return {"status": "ok"}

    webhook_event = existing_event or WebhookEvent(
        provider="razorpay",
        external_event_id=external_event_id,
        event_type=event_type,
        payload=payload,
    )
    db.add(webhook_event)

    if event_type in {"payment.failed", "payment.captured", "payment.authorized"}:
        _upsert_payment_from_event(db=db, payload=payload, event_type=event_type)

    webhook_event.processed_at = datetime.now(UTC)
    db.commit()

    return {"status": "ok"}


def _upsert_payment_from_event(*, db: Session, payload: dict[str, Any], event_type: str) -> None:
    payment_payload = payload.get("payload", {}).get("payment", {}).get("entity", {})
    if not isinstance(payment_payload, dict):
        raise HTTPException(status_code=400, detail="Webhook payment entity is missing")

    razorpay_order_id = payment_payload.get("order_id")
    if not razorpay_order_id:
        raise HTTPException(status_code=400, detail="Webhook payment order ID is missing")

    order = db.scalar(select(Order).where(Order.external_order_id == razorpay_order_id))
    if order is None:
        raise HTTPException(status_code=404, detail="Referenced internal order not found")

    external_payment_id = payment_payload.get("id")
    if not external_payment_id:
        raise HTTPException(status_code=400, detail="Webhook payment ID is missing")

    payment = db.scalar(select(Payment).where(Payment.external_payment_id == external_payment_id))
    if payment is None:
        payment = Payment(
            merchant_id=order.merchant_id,
            customer_id=order.customer_id,
            order_id=order.id,
            external_payment_id=external_payment_id,
            amount=int(payment_payload.get("amount") or order.amount),
            currency=str(payment_payload.get("currency") or order.currency).upper(),
            retry_count=0,
            status=PaymentStatus.pending,
        )
        db.add(payment)

    payment.merchant_id = order.merchant_id
    payment.customer_id = order.customer_id
    payment.order_id = order.id
    payment.amount = int(payment_payload.get("amount") or order.amount)
    payment.currency = str(payment_payload.get("currency") or order.currency).upper()
    payment.payment_method = payment_payload.get("method")

    if event_type == "payment.failed":
        payment.status = PaymentStatus.failed
        payment.failure_reason = _failure_reason(payment_payload)
    elif event_type == "payment.captured":
        payment.status = PaymentStatus.successful
        payment.failure_reason = None
    else:
        payment.status = PaymentStatus.pending


def _failure_reason(payment_payload: dict[str, Any]) -> str | None:
    for key in ("error_description", "error_reason", "error_code", "description"):
        value = payment_payload.get(key)
        if value:
            return str(value)
    return None
