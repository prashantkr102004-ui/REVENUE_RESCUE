from app.db.session import SessionLocal
from app.services.demo_seed import get_or_create_demo_customer


def main() -> None:
    db = SessionLocal()
    try:
        customer = get_or_create_demo_customer(db)
        db.commit()
        print(f"Demo customer UUID: {customer.id}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
