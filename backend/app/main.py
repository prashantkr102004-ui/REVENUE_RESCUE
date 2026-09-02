import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.core.config import get_settings


settings = get_settings()
logger = logging.getLogger(__name__)

app = FastAPI(title="RevenueRescue AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(api_router)


@app.on_event("startup")
def log_razorpay_env_debug() -> None:
    logger.warning(
        "TEMP Razorpay env debug: key_id_exists=%s key_id_prefix=%s key_secret_exists=%s key_secret_length=%s",
        bool(settings.razorpay_key_id),
        settings.razorpay_key_id[:8] if settings.razorpay_key_id else "",
        bool(settings.razorpay_key_secret),
        len(settings.razorpay_key_secret),
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}
