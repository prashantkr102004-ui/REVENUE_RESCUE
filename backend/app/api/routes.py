from fastapi import APIRouter

from app.api.v1.dev import router as dev_router
from app.api.v1.payments import router as payments_router
from app.api.v1.recovery_cases import router as recovery_cases_router
from app.api.v1.webhooks import router as webhooks_router

api_router = APIRouter(prefix="/api")
api_router.include_router(dev_router)
api_router.include_router(payments_router)
api_router.include_router(recovery_cases_router)
api_router.include_router(webhooks_router)
