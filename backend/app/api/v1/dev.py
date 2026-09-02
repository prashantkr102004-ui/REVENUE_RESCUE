import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.demo_seed import get_or_create_demo_customer

router = APIRouter(prefix="/dev", tags=["dev"])


class DemoCustomerResponse(BaseModel):
    customer_id: uuid.UUID
    name: str | None
    email: str | None


@router.post("/demo-customer", response_model=DemoCustomerResponse)
def create_demo_customer(db: Session = Depends(get_db)) -> DemoCustomerResponse:
    customer = get_or_create_demo_customer(db)
    db.commit()
    db.refresh(customer)
    return DemoCustomerResponse(customer_id=customer.id, name=customer.name, email=customer.email)
