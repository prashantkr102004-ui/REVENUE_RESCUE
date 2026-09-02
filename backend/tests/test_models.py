from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.customer import Customer
from app.models.merchant import Merchant
from app.models.order import Order
from app.models.payment import Payment, PaymentStatus
from app.models.recovery_action import RecoveryAction, RecoveryActionStatus, RecoveryActionType
from app.models.recovery_case import RecoveryCase, RecoveryCaseStatus


def test_database_model_creation(db_session: Session) -> None:
    merchant = Merchant(name="Acme Fintech", email="ops@example.com")
    customer = Customer(
        merchant=merchant,
        external_customer_id=None,
        name="Priya Kapoor",
        email="priya@example.com",
        phone="+919999999999",
        customer_value_score=Decimal("91.50"),
        successful_payments=4,
        failed_payments=1,
    )
    order = Order(
        merchant=merchant,
        customer=customer,
        external_order_id=None,
        amount=499900,
        currency="INR",
        status="created",
    )
    payment = Payment(
        merchant=merchant,
        customer=customer,
        order=order,
        external_payment_id=None,
        amount=499900,
        currency="INR",
        payment_method="upi",
        status=PaymentStatus.failed,
        failure_reason="bank_declined",
        retry_count=0,
    )
    recovery_case = RecoveryCase(
        merchant=merchant,
        customer=customer,
        payment=payment,
        status=RecoveryCaseStatus.open,
        revenue_at_risk=499900,
        recovery_probability=None,
        recommended_action=None,
    )
    action = RecoveryAction(
        recovery_case=recovery_case,
        action_type=RecoveryActionType.retry,
        status=RecoveryActionStatus.proposed,
        reason="Initial recovery attempt",
        retry_number=1,
    )
    audit_log = AuditLog(
        merchant=merchant,
        recovery_case=recovery_case,
        event_type="recovery_case.created",
        description="Recovery case opened for failed payment.",
        metadata_={"source": "test"},
    )

    db_session.add_all([merchant, customer, order, payment, recovery_case, action, audit_log])
    db_session.commit()

    assert merchant.id is not None
    assert order.amount == 499900
    assert payment.amount == 499900
    assert recovery_case.revenue_at_risk == 499900
    assert recovery_case.payment == payment
    assert recovery_case.actions == [action]
    assert audit_log.metadata_ == {"source": "test"}
