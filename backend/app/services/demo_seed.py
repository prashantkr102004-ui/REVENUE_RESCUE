from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.merchant import Merchant


DEMO_MERCHANT_EMAIL = "demo-store@revenuerescue.local"
DEMO_CUSTOMER_EMAIL = "demo@revenuerescue.local"


def get_or_create_demo_customer(db: Session) -> Customer:
    merchant = db.scalar(select(Merchant).where(Merchant.email == DEMO_MERCHANT_EMAIL))
    if merchant is None:
        merchant = Merchant(name="RevenueRescue Demo Store", email=DEMO_MERCHANT_EMAIL)
        db.add(merchant)
        db.flush()

    customer = db.scalar(
        select(Customer).where(
            Customer.merchant_id == merchant.id,
            Customer.email == DEMO_CUSTOMER_EMAIL,
        )
    )
    if customer is None:
        customer = Customer(
            merchant_id=merchant.id,
            name="Demo Customer",
            email=DEMO_CUSTOMER_EMAIL,
            successful_payments=0,
            failed_payments=0,
        )
        db.add(customer)
        db.flush()

    return customer
