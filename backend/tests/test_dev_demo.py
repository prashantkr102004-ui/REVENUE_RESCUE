from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.customer import Customer


def test_create_demo_customer_returns_reusable_customer(client: TestClient, db_session: Session) -> None:
    first_response = client.post("/api/dev/demo-customer")
    second_response = client.post("/api/dev/demo-customer")

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json()["customer_id"] == second_response.json()["customer_id"]
    assert first_response.json()["email"] == "demo@revenuerescue.local"
    assert len(db_session.scalars(select(Customer)).all()) == 1
