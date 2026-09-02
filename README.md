# RevenueRescue AI

RevenueRescue AI is a hackathon MVP for helping merchants recover revenue from failed online payments.

The idea is simple: when a customer's payment fails, the system should eventually detect the failure, understand the risk, recommend the best recovery action, and help the merchant recover the payment without losing visibility or control.

For this stage of the project, we have built the foundation:

- A Next.js dashboard-style frontend
- A FastAPI backend
- PostgreSQL database models for merchants, customers, orders, payments, recovery cases, recovery actions, audit logs, and webhook events
- Alembic migrations
- Razorpay Test Mode order creation
- Razorpay webhook handling with signature verification
- Razorpay Checkout test flow from the frontend
- Backend tests for health checks, database behavior, recovery cases, Razorpay order creation, webhooks, and payment verification

This is intentionally not a full production product yet. AI scoring, recovery workflows, authentication, Redis, Kafka, and full merchant dashboards are planned future layers.

## How It Works Today

In the current MVP flow:

1. A demo customer is created in the database.
2. The frontend test payment page asks the backend to create a Razorpay order.
3. The backend creates an internal order and a Razorpay Test Mode order.
4. Razorpay Checkout opens in the browser.
5. After a successful test payment, the frontend sends the Razorpay payment details to the backend.
6. The backend verifies the payment signature before marking the payment successful.
7. Razorpay webhooks can also update payment status safely without creating duplicate payment rows.

All money amounts are stored in the smallest currency unit, such as paise for INR. The backend never stores money as floating point values.

## Project Structure

```text
RevenueRescue-AI/
  backend/
  frontend/
  .env.example
  .gitignore
  docker-compose.yml
  README.md
```

## Tech Stack

Frontend:

- Next.js
- TypeScript
- Tailwind CSS
- App Router

Backend:

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic

Database:

- PostgreSQL

Payments:

- Razorpay Test Mode

## Environment Setup

Create a `.env` file in the project root using `.env.example` as a reference.

Do not commit real secrets to Git.

## Backend

```bash
cd RevenueRescue-AI/backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Health check:

```bash
curl http://localhost:8000/health
```

API docs:

```text
http://localhost:8000/docs
```

## Database

Start development PostgreSQL:

```bash
cd RevenueRescue-AI
docker compose up -d postgres
```

Run migrations:

```bash
cd RevenueRescue-AI/backend
alembic upgrade head
```

Seed a demo merchant and customer:

```bash
cd RevenueRescue-AI/backend
python scripts/seed_demo.py
```

The seed command prints a demo customer UUID. Use that UUID on the test payment page.

## Frontend

```bash
cd RevenueRescue-AI/frontend
npm install
npm run dev
```

Open:

```text
http://localhost:3000
```

Test payments:

```text
http://localhost:3000/payments/test
```

## Tests

Backend:

```bash
cd RevenueRescue-AI/backend
pytest
```

Frontend checks:

```bash
cd RevenueRescue-AI/frontend
npm run lint
npm run build
```
