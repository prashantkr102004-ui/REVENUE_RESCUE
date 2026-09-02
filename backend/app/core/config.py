from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = Field(
        default="revenuerescue-api",
        validation_alias=AliasChoices("BACKEND_SERVICE_NAME", "SERVICE_NAME"),
    )
    cors_origins: str = Field(
        default="http://localhost:3000",
        validation_alias=AliasChoices("BACKEND_CORS_ORIGINS", "CORS_ORIGINS"),
    )
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/revenuerescue"
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_prefix="",
        extra="ignore",
        populate_by_name=True,
    )

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
