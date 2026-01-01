from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "ads-aggregator"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    database_url: str = "postgresql+psycopg2://postgres:postgres@db:5432/ads"
    redis_url: str = "redis://redis:6379/0"

    celery_broker_url: str | None = None
    celery_result_backend: str | None = None

    yandex_reports_url: str = "https://api.direct.yandex.com/json/v5/reports"
    yandex_reports_token: str | None = None
    yandex_reports_skip_header: bool = True

    dev_mode: bool = False
    cors_origins: str = "*"
    env: str = "dev"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if settings.celery_broker_url is None:
        settings.celery_broker_url = settings.redis_url
    if settings.celery_result_backend is None:
        settings.celery_result_backend = settings.redis_url
    return settings
