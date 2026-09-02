import hashlib
import hmac
import json
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.payments import get_razorpay_service as get_payments_razorpay_service
from app.api.v1.webhooks import get_razorpay_service as get_webhooks_razorpay_service
from app.core.config import Settings
from app.db.session import get_db
from app.main import app
from app.models.customer import Customer
from app.models.merchant import Merchant
from app.models.order import Order
from app.models.payment import Payment, PaymentStatus
from app.models.webhook_event import WebhookEvent
from app.services.razorpay_service import RazorpayService

TEST_WEBHOOK_SECRET = "test_webhook_secret"
TEST_KEY_SECRET = "test_key_secret"


class FakeRazorpayService:
    key_id = "rzp_test_mock_key"

    def create_order(self, *, amount: int, currency: str, receipt: str) -> dict:
        return {
            "id": "order_mock_123",
            "amount": amount,
            "currency": currency,
            "receipt": receipt,
        }


def test_create_order_succeeds_with_mocked_razorpay(client: TestClient, db_session: Session) -> None:
    customer = _create_customer(db_session)
    app.dependency_overrides[get_payments_razorpay_service] = lambda: FakeRazorpayService()

    response = client.post(
        "/api/payments/create-order",
        json={"customer_id": str(customer.id), "amount": 499900, "currency": "INR"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["razorpay_order_id"] == "order_mock_123"
    assert body["amount"] == 499900
    assert body["currency"] == "INR"
    assert body["razorpay_key_id"] == "rzp_test_mock_key"

    order = db_session.get(Order, uuid.UUID(body["internal_order_id"]))
    assert order is not None
    assert order.customer_id == customer.id
    assert order.merchant_id == customer.merchant_id
    assert order.amount == 499900
    assert order.external_order_id == "order_mock_123"


def test_create_order_returns_404_for_unknown_customer(client: TestClient) -> None:
    app.dependency_overrides[get_payments_razorpay_service] = lambda: FakeRazorpayService()

    response = client.post(
        "/api/payments/create-order",
        json={"customer_id": "00000000-0000-0000-0000-000000000001", "amount": 499900, "currency": "INR"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Customer not found"}


def test_valid_payment_failed_webhook_creates_payment(client: TestClient, db_session: Session) -> None:
    order = _create_order(db_session, external_order_id="order_failed_123")
    payload = _payment_payload(
        event="payment.failed",
        event_id="evt_failed_123",
        order_id="order_failed_123",
        payment_id="pay_failed_123",
        status="failed",
        error_description="Payment failed due to insufficient funds.",
    )

    response = _post_signed_webhook(client, payload)

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    payment = db_session.scalar(select(Payment).where(Payment.external_payment_id == "pay_failed_123"))
    assert payment is not None
    assert payment.order_id == order.id
    assert payment.merchant_id == order.merchant_id
    assert payment.customer_id == order.customer_id
    assert payment.amount == 499900
    assert payment.currency == "INR"
    assert payment.payment_method == "upi"
    assert payment.status == PaymentStatus.failed
    assert payment.failure_reason == "Payment failed due to insufficient funds."


def test_valid_payment_captured_webhook_updates_payment(client: TestClient, db_session: Session) -> None:
    order = _create_order(db_session, external_order_id="order_captured_123")
    existing_payment = Payment(
        merchant_id=order.merchant_id,
        customer_id=order.customer_id,
        order_id=order.id,
        external_payment_id="pay_captured_123",
        amount=499900,
        currency="INR",
        payment_method="upi",
        status=PaymentStatus.failed,
        failure_reason="previous failure",
        retry_count=0,
    )
    db_session.add(existing_payment)
    db_session.commit()

    payload = _payment_payload(
        event="payment.captured",
        event_id="evt_captured_123",
        order_id="order_captured_123",
        payment_id="pay_captured_123",
        status="captured",
    )

    response = _post_signed_webhook(client, payload)

    assert response.status_code == 200
    payment = db_session.scalar(select(Payment).where(Payment.external_payment_id == "pay_captured_123"))
    assert payment is not None
    assert payment.status == PaymentStatus.successful
    assert payment.failure_reason is None
    assert payment.retry_count == 0


def test_invalid_webhook_signature_returns_400(client: TestClient) -> None:
    app.dependency_overrides[get_webhooks_razorpay_service] = lambda: RazorpayService(
        Settings(razorpay_webhook_secret=TEST_WEBHOOK_SECRET)
    )

    response = client.post(
        "/api/webhooks/razorpay",
        content=json.dumps({"event": "payment.failed"}).encode("utf-8"),
        headers={"X-Razorpay-Signature": "invalid", "Content-Type": "application/json"},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid Razorpay webhook signature"}


def test_duplicate_webhook_does_not_duplicate_payment(client: TestClient, db_session: Session) -> None:
    _create_order(db_session, external_order_id="order_duplicate_123")
    payload = _payment_payload(
        event="payment.failed",
        event_id="evt_duplicate_123",
        order_id="order_duplicate_123",
        payment_id="pay_duplicate_123",
        status="failed",
    )

    first_response = _post_signed_webhook(client, payload)
    second_response = _post_signed_webhook(client, payload)

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert len(db_session.scalars(select(Payment).where(Payment.external_payment_id == "pay_duplicate_123")).all()) == 1
    assert len(db_session.scalars(select(WebhookEvent).where(WebhookEvent.external_event_id == "evt_duplicate_123")).all()) == 1


def test_valid_payment_verification_creates_successful_payment(client: TestClient, db_session: Session) -> None:
    order = _create_order(db_session, external_order_id="order_verify_123")

    response = _post_payment_verification(
        client,
        razorpay_order_id="order_verify_123",
        razorpay_payment_id="pay_verify_123",
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "verified"
    assert body["order_id"] == str(order.id)

    payment = db_session.scalar(select(Payment).where(Payment.external_payment_id == "pay_verify_123"))
    assert payment is not None
    assert payment.status == PaymentStatus.successful
    assert payment.order_id == order.id
    assert payment.amount == 499900
    assert payment.currency == "INR"


def test_invalid_payment_signature_returns_400(client: TestClient) -> None:
    app.dependency_overrides[get_payments_razorpay_service] = lambda: RazorpayService(
        Settings(razorpay_key_secret=TEST_KEY_SECRET)
    )

    response = client.post(
        "/api/payments/verify",
        json={
            "razorpay_payment_id": "pay_invalid_signature_123",
            "razorpay_order_id": "order_invalid_signature_123",
            "razorpay_signature": "invalid",
        },
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid Razorpay payment signature"}


def test_payment_verification_returns_404_for_unknown_razorpay_order(client: TestClient) -> None:
    response = _post_payment_verification(
        client,
        razorpay_order_id="order_unknown_123",
        razorpay_payment_id="pay_unknown_order_123",
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Referenced internal order not found"}


def test_duplicate_payment_verification_does_not_duplicate_payment(client: TestClient, db_session: Session) -> None:
    _create_order(db_session, external_order_id="order_verify_duplicate_123")

    first_response = _post_payment_verification(
        client,
        razorpay_order_id="order_verify_duplicate_123",
        razorpay_payment_id="pay_verify_duplicate_123",
    )
    second_response = _post_payment_verification(
        client,
        razorpay_order_id="order_verify_duplicate_123",
        razorpay_payment_id="pay_verify_duplicate_123",
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    payments = db_session.scalars(
        select(Payment).where(Payment.external_payment_id == "pay_verify_duplicate_123")
    ).all()
    assert len(payments) == 1
    assert payments[0].retry_count == 0


def test_webhook_and_frontend_verification_do_not_duplicate_payment(client: TestClient, db_session: Session) -> None:
    _create_order(db_session, external_order_id="order_webhook_and_verify_123")
    payload = _payment_payload(
        event="payment.captured",
        event_id="evt_webhook_and_verify_123",
        order_id="order_webhook_and_verify_123",
        payment_id="pay_webhook_and_verify_123",
        status="captured",
    )

    webhook_response = _post_signed_webhook(client, payload)
    verification_response = _post_payment_verification(
        client,
        razorpay_order_id="order_webhook_and_verify_123",
        razorpay_payment_id="pay_webhook_and_verify_123",
    )

    assert webhook_response.status_code == 200
    assert verification_response.status_code == 200
    payments = db_session.scalars(
        select(Payment).where(Payment.external_payment_id == "pay_webhook_and_verify_123")
    ).all()
    assert len(payments) == 1
    assert payments[0].status == PaymentStatus.successful


def _create_customer(db_session: Session) -> Customer:
    merchant = Merchant(name="Acme Fintech", email="merchant@example.com")
    customer = Customer(merchant=merchant, name="Test Customer", email="customer@example.com")
    db_session.add_all([merchant, customer])
    db_session.commit()
    db_session.refresh(customer)
    return customer


def _create_order(db_session: Session, *, external_order_id: str) -> Order:
    customer = _create_customer(db_session)
    order = Order(
        merchant_id=customer.merchant_id,
        customer_id=customer.id,
        external_order_id=external_order_id,
        amount=499900,
        currency="INR",
        status="created",
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    return order


def _payment_payload(
    *,
    event: str,
    event_id: str,
    order_id: str,
    payment_id: str,
    status: str,
    error_description: str | None = None,
) -> dict:
    entity = {
        "id": payment_id,
        "order_id": order_id,
        "amount": 499900,
        "currency": "INR",
        "method": "upi",
        "status": status,
    }
    if error_description:
        entity["error_description"] = error_description

    return {
        "id": event_id,
        "event": event,
        "payload": {
            "payment": {
                "entity": entity,
            }
        },
    }


def _post_signed_webhook(client: TestClient, payload: dict):
    app.dependency_overrides[get_webhooks_razorpay_service] = lambda: RazorpayService(
        Settings(razorpay_webhook_secret=TEST_WEBHOOK_SECRET)
    )
    raw_body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    signature = hmac.new(TEST_WEBHOOK_SECRET.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return client.post(
        "/api/webhooks/razorpay",
        content=raw_body,
        headers={"X-Razorpay-Signature": signature, "Content-Type": "application/json"},
    )


def _post_payment_verification(client: TestClient, *, razorpay_order_id: str, razorpay_payment_id: str):
    app.dependency_overrides[get_payments_razorpay_service] = lambda: RazorpayService(
        Settings(razorpay_key_secret=TEST_KEY_SECRET)
    )
    signature = hmac.new(
        TEST_KEY_SECRET.encode("utf-8"),
        f"{razorpay_order_id}|{razorpay_payment_id}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return client.post(
        "/api/payments/verify",
        json={
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_order_id": razorpay_order_id,
            "razorpay_signature": signature,
        },
    )
