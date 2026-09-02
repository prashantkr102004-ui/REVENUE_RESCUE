import uuid

from pydantic import BaseModel, Field


class CreateRazorpayOrderRequest(BaseModel):
    customer_id: uuid.UUID
    amount: int = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)


class CreateRazorpayOrderResponse(BaseModel):
    internal_order_id: uuid.UUID
    razorpay_order_id: str
    amount: int
    currency: str
    razorpay_key_id: str


class VerifyRazorpayPaymentRequest(BaseModel):
    razorpay_payment_id: str
    razorpay_order_id: str
    razorpay_signature: str


class VerifyRazorpayPaymentResponse(BaseModel):
    status: str
    payment_id: uuid.UUID
    order_id: uuid.UUID
