# RevenueRescue AI

Autonomous revenue recovery foundation for the Razorpay hackathon.

## Project Structure

```text
RevenueRescue-AI/
  backend/
  frontend/
  .env.example
  .gitignore
  README.md
```

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

## Frontend

```bash
cd RevenueRescue-AI/frontend
npm install
npm run dev
```

Open http://localhost:3000.

Test payments: http://localhost:3000/payments/test.

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
