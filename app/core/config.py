from functools import lru_cache

from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "ads-aggregator"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/ads"
    redis_url: str = "redis://localhost:6379/0"

    default_organization_id: int = 1

    celery_broker_url: str | None = None
    celery_result_backend: str | None = None

    yandex_reports_url: str = "https://api.direct.yandex.com/json/v5/reports"
    yandex_reports_token: str | None = None
    yandex_reports_skip_header: bool = True

    dev_mode: bool = False
    cors_origins: str = "*"
    env: str = "dev"
    secret_key: str = Field(default="dev_secret", validation_alias=AliasChoices("SECRET_KEY", "JWT_SECRET"))
    access_token_expire_minutes: int = Field(
        default=60,
        validation_alias=AliasChoices("ACCESS_TTL_MIN", "ACCESS_TOKEN_EXPIRE_MINUTES"),
    )
    access_token_algorithm: str = Field(
        default="HS256",
        validation_alias=AliasChoices("JWT_ALG", "ACCESS_TOKEN_ALGORITHM"),
    )
    refresh_token_ttl_days: int = Field(
        default=7,
        validation_alias=AliasChoices("REFRESH_TTL_DAYS", "REFRESH_TOKEN_TTL_DAYS"),
    )
    web_base_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("WEB_BASE_URL", "FRONTEND_BASE_URL"),
    )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if settings.celery_broker_url is None:
        settings.celery_broker_url = settings.redis_url
    if settings.celery_result_backend is None:
        settings.celery_result_backend = settings.redis_url
    return settings
