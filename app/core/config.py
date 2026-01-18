from functools import lru_cache
import logging

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
    enable_dev_endpoints: bool = Field(
        default=False,
        validation_alias=AliasChoices("ENABLE_DEV_ENDPOINTS"),
    )
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
    email_send_mode: str = Field(
        default="smtp",
        validation_alias=AliasChoices("EMAIL_SEND_MODE", "EMAIL_BACKEND"),
    )
    smtp_host: str | None = Field(
        default=None,
        validation_alias=AliasChoices("SMTP_HOST", "MAIL_HOST"),
    )
    smtp_port: int = Field(
        default=25,
        validation_alias=AliasChoices("SMTP_PORT", "MAIL_PORT"),
    )
    smtp_user: str | None = Field(
        default=None,
        validation_alias=AliasChoices("SMTP_USER", "MAIL_USER"),
    )
    smtp_password: str | None = Field(
        default=None,
        validation_alias=AliasChoices("SMTP_PASSWORD", "MAIL_PASSWORD"),
    )
    smtp_from: str = Field(
        default="no-reply@example.com",
        validation_alias=AliasChoices("SMTP_FROM", "MAIL_FROM"),
    )
    smtp_use_tls: bool = Field(
        default=False,
        validation_alias=AliasChoices("SMTP_USE_TLS", "MAIL_USE_TLS"),
    )
    smtp_use_ssl: bool = Field(
        default=False,
        validation_alias=AliasChoices("SMTP_USE_SSL", "MAIL_USE_SSL"),
    )
    smtp_timeout_seconds: int = Field(
        default=10,
        validation_alias=AliasChoices("SMTP_TIMEOUT", "MAIL_TIMEOUT"),
    )

    credentials_enc_keys: str | None = Field(
        default=None,
        validation_alias=AliasChoices("CREDENTIALS_ENC_KEYS"),
    )
    credentials_enc_active_kid: str | None = Field(
        default=None,
        validation_alias=AliasChoices("CREDENTIALS_ENC_ACTIVE_KID"),
    )

    demo_email: str = Field(
        default="demo@example.com",
        validation_alias=AliasChoices("DEMO_EMAIL"),
    )
    demo_password: str = Field(
        default="demo12345",
        validation_alias=AliasChoices("DEMO_PASSWORD"),
    )
    demo_org_name: str = Field(
        default="Демо-организация",
        validation_alias=AliasChoices("DEMO_ORG_NAME"),
    )
    demo_connections: str = Field(
        default="Яндекс.Директ: Демо 1,Яндекс.Директ: Демо 2",
        validation_alias=AliasChoices("DEMO_CONNECTIONS"),
    )
    demo_force_password: bool = Field(
        default=False,
        validation_alias=AliasChoices("DEMO_FORCE_PASSWORD"),
    )

    # AI Keys
    openai_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OPENAI_API_KEY"),
    )
    anthropic_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ANTHROPIC_API_KEY"),
    )

    # Integrations
    telegram_bot_token: str | None = Field(
        default=None,
        validation_alias=AliasChoices("TELEGRAM_BOT_TOKEN"),
    )
    telegram_admin_chat_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("TELEGRAM_ADMIN_CHAT_ID"),
    )
    yandex_metrica_client_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("YANDEX_METRICA_CLIENT_ID"),
    )
    yandex_metrica_client_secret: str | None = Field(
        default=None,
        validation_alias=AliasChoices("YANDEX_METRICA_CLIENT_SECRET"),
    )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if settings.celery_broker_url is None:
        settings.celery_broker_url = settings.redis_url
    if settings.celery_result_backend is None:
        settings.celery_result_backend = settings.redis_url
    if settings.env == "prod" and not settings.credentials_enc_keys:
        raise ValueError("CREDENTIALS_ENC_KEYS is required in prod")
    if settings.env != "prod" and not settings.credentials_enc_keys:
        logging.getLogger(__name__).warning(
            "CREDENTIALS_ENC_KEYS is not set; credentials will be stored in plaintext."
        )
    return settings
