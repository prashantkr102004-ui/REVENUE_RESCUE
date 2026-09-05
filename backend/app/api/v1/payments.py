import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.customer import Customer
from app.models.order import Order
from app.models.payment import Payment, PaymentStatus
from app.schemas.payment import (
    CreateRazorpayOrderRequest,
    CreateRazorpayOrderResponse,
    OrderPaymentStateResponse,
    VerifyRazorpayPaymentRequest,
    VerifyRazorpayPaymentResponse,
)
from app.services.razorpay_service import RazorpayService, RazorpayServiceError, RazorpaySignatureError
from sqlalchemy import select

router = APIRouter(prefix="/payments", tags=["payments"])


def get_razorpay_service() -> RazorpayService:
    return RazorpayService(get_settings())


@router.post("/create-order", response_model=CreateRazorpayOrderResponse)
def create_order(
    payload: CreateRazorpayOrderRequest,
    db: Session = Depends(get_db),
    razorpay_service: RazorpayService = Depends(get_razorpay_service),
) -> CreateRazorpayOrderResponse:
    customer = db.get(Customer, payload.customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    order = Order(
        merchant_id=customer.merchant_id,
        customer_id=customer.id,
        amount=payload.amount,
        currency=payload.currency.upper(),
        status="created",
    )
    db.add(order)
    db.flush()

    try:
        razorpay_order = razorpay_service.create_order(
            amount=order.amount,
            currency=order.currency,
            receipt=str(order.id),
        )
    except RazorpayServiceError as exc:
        db.rollback()
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    razorpay_order_id = razorpay_order.get("id")
    if not razorpay_order_id:
        db.rollback()
        raise HTTPException(status_code=502, detail="Razorpay order response did not include an order ID")

    order.external_order_id = razorpay_order_id
    db.commit()
    db.refresh(order)

    return CreateRazorpayOrderResponse(
        internal_order_id=order.id,
        razorpay_order_id=razorpay_order_id,
        amount=order.amount,
        currency=order.currency,
        razorpay_key_id=razorpay_service.key_id,
    )


@router.get("/order/{internal_order_id}", response_model=OrderPaymentStateResponse)
def get_order_payment_state(
    internal_order_id: str,
    db: Session = Depends(get_db),
) -> OrderPaymentStateResponse:
    try:
        order_id = uuid.UUID(internal_order_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid order ID") from exc

    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    payment = db.scalar(
        select(Payment)
        .where(Payment.order_id == order.id)
        .order_by(Payment.updated_at.desc(), Payment.created_at.desc())
    )

    return OrderPaymentStateResponse(
        status=payment.status.value if payment else None,
        failure_reason=payment.failure_reason if payment else None,
        payment_method=payment.payment_method if payment else None,
        external_payment_id=payment.external_payment_id if payment else None,
        amount=payment.amount if payment else order.amount,
        currency=payment.currency if payment else order.currency,
    )


@router.post("/verify", response_model=VerifyRazorpayPaymentResponse)
def verify_payment(
    payload: VerifyRazorpayPaymentRequest,
    db: Session = Depends(get_db),
    razorpay_service: RazorpayService = Depends(get_razorpay_service),
) -> VerifyRazorpayPaymentResponse:
    try:
        razorpay_service.verify_payment_signature(
            razorpay_order_id=payload.razorpay_order_id,
            razorpay_payment_id=payload.razorpay_payment_id,
            razorpay_signature=payload.razorpay_signature,
        )
    except RazorpaySignatureError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    order = db.scalar(select(Order).where(Order.external_order_id == payload.razorpay_order_id))
    if order is None:
        raise HTTPException(status_code=404, detail="Referenced internal order not found")

    payment = db.scalar(select(Payment).where(Payment.external_payment_id == payload.razorpay_payment_id))
    if payment is None:
        payment = Payment(
            merchant_id=order.merchant_id,
            customer_id=order.customer_id,
            order_id=order.id,
            external_payment_id=payload.razorpay_payment_id,
            amount=order.amount,
            currency=order.currency,
            retry_count=0,
            status=PaymentStatus.successful,
        )
        db.add(payment)

    payment.merchant_id = order.merchant_id
    payment.customer_id = order.customer_id
    payment.order_id = order.id
    payment.amount = order.amount
    payment.currency = order.currency
    payment.status = PaymentStatus.successful
    payment.failure_reason = None

    db.commit()
    db.refresh(payment)

    return VerifyRazorpayPaymentResponse(status="verified", payment_id=payment.id, order_id=order.id)
