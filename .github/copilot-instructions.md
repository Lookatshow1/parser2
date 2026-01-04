This repository is an Ads Aggregator service built with FastAPI, SQLAlchemy, Celery and a Next.js frontend.

High-level architecture
- **API (FastAPI):** `app/main.py` composes routers under `/api/*` (see `app/api/`). Use `create_app()` to inspect middleware and global exception handlers.
- **Data layer:** SQLAlchemy models live in `app/db/models.py` and use `app/db/base.py` for Base. Migrations via Alembic (`alembic/`), run `docker compose run --rm api alembic upgrade head`.
- **Connectors:** Platform-specific connector implementations are in `app/connectors/` (e.g. `yandex_direct.py`, `vk_ads.py`, `ozon_performance.py`). `app/services/connector_service.py` maps `Platform` enum to connector instances.
- **Business logic / services:** Reusable logic lives under `app/services/` (e.g. `connector_service.py`, `event_service.py`). Prefer adding domain logic there rather than in route handlers.
- **Background jobs:** Celery tasks live in `app/workers/` (e.g. `yandex_tasks.py`). Celery broker/result backend default to Redis (see `app/core/config.py`).
- **Frontend:** Next.js app in `apps/web` reads `NEXT_PUBLIC_API_BASE_URL` to call backend.

Quick dev workflows
- Start everything (recommended): `cp .env.example .env && docker compose up --build`
- Apply DB migrations inside containers: `docker compose run --rm api alembic upgrade head`
- Run backend locally (without Docker): ensure `.env` is present and run app via Uvicorn pointing to `app.main:app`.
- Run frontend: `cd apps/web && cp .env.example .env && npm install && npm run dev`.
- Run tests: `pytest` from repo root.
- Helper scripts: `./scripts/self_test.sh`, `./scripts/smoke_test.sh`, `./scripts/seed_dev.sh`.

Key patterns & conventions (project-specific)
- Settings: configuration uses a cached Pydantic settings object `get_settings()` in `app/core/config.py`. Read environment values from `.env` when adding new config.
- Connectors contract: implement a connector class that behaves like the existing ones (see `app/connectors/stub.py` for minimal implementation). Register new connectors in `app/services/connector_service.py` mapped by `Platform` enum.
- Routers: each API area has its own router file under `app/api/` (e.g. `events.py`, `integrations.py`). Add routes by creating a router and including it in `app/main.py`'s API router.
- Background jobs: use Celery tasks defined in `app/workers/` and trigger them via `.delay()`; Celery config is loaded from `get_settings()`.
- DB models: models use typed SQLAlchemy `Mapped[...]` fields. When adding migrations, update `alembic/versions/` with generated scripts.

Integration points & external dependencies
- Postgres: `database_url` configured in `app/core/config.py` (default `postgresql+psycopg2://...`).
- Redis: used for Celery and caching; `redis_url` in settings.
- Yandex Reports API: connector uses `yandex_reports_url` and `yandex_reports_token` settings; see `app/connectors/yandex_direct.py`.
- Frontend: `apps/web` reads `NEXT_PUBLIC_API_BASE_URL` — ensure CORS via `cors_origins` setting.

Debugging tips
- Health & openapi: `GET /healthz`, `GET /api/health`, `GET /openapi.json`.
- If connectors fail, inspect `Connection` and `ConnectionStatus` records in DB (`app/db/models.py`).
- To debug Celery tasks locally, ensure Redis is reachable and run a worker inside the `api` container or locally with same env.

Files to inspect for common changes
- `app/main.py` — app composition, routers, exception handlers.
- `app/core/config.py` — env-driven configuration.
- `app/connectors/` — platform integrations.
- `app/services/` — business/service layer (preferred place for logic).
- `app/workers/` — celery tasks and periodic syncs.
- `app/db/models.py` and `alembic/` — schema and migrations.

Examples
- Add a new connector: implement `app/connectors/my_platform.py`, update `Platform` enum in `app/db/models.py` and register in `app/services/connector_service.py`.
- Add API routes: create `app/api/my_area.py` with an `APIRouter` and include it in `app/main.py`'s API router.

When in doubt
- Prefer following existing modules (look at `events.py`, `integrations.py`, `connectors.py`) for idiomatic patterns.
- Ask for clarification if an external credential or secret is needed — do not hardcode tokens in code.

If anything here is unclear or you'd like more details (e.g., explicit examples for adding a connector or running Celery locally), tell me which section to expand.
