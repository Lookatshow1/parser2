from fastapi import FastAPI, Request, HTTPException, APIRouter
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder

from app.api.connections import router as connections_router
from app.api.connectors import router as connectors_router
from app.api.compliance import router as compliance_router
from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.orgs import router as orgs_router
from app.api.invites import router as invites_router
from app.api.erir import router as erir_router
from app.api.dev import router as dev_router
from app.api.events import router as events_router
from app.api.experiments import router as experiments_router
from app.api.health import router as health_router
from app.api.integrations import router as integrations_router
from app.api.metrics import router as metrics_router
from app.api.plans import router as plans_router
from app.api.jobs import router as jobs_router
from app.api.sync_runs import router as sync_runs_router
from app.api.me import router as me_router
from app.api.schemas import ApiCapabilitiesResponse, ApiVersionResponse, HealthResponse, YandexSyncMetricsRequest
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.workers.yandex_tasks import sync_yandex_metrics


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="Ads Aggregator API")
    settings = get_settings()
    origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router)
    api_router = APIRouter(prefix="/api")
    api_router.include_router(health_router)
    api_router.include_router(auth_router)
    api_router.include_router(me_router)
    api_router.include_router(orgs_router)
    api_router.include_router(invites_router)
    api_router.include_router(connections_router)
    api_router.include_router(connectors_router)
    api_router.include_router(compliance_router)
    api_router.include_router(dashboard_router)
    api_router.include_router(erir_router)
    api_router.include_router(events_router)
    api_router.include_router(experiments_router)
    api_router.include_router(integrations_router)
    api_router.include_router(metrics_router)
    api_router.include_router(plans_router)
    api_router.include_router(dev_router)
    api_router.include_router(jobs_router)
    api_router.include_router(sync_runs_router)

    @api_router.get("/version", response_model=ApiVersionResponse)
    def api_version():
        return ApiVersionResponse(version="0.1.0")

    @api_router.get("/capabilities", response_model=ApiCapabilitiesResponse)
    def api_capabilities():
        return ApiCapabilitiesResponse(
            platforms=["yandex", "ozon", "vk", "stub"],
            operations={
                "create_campaign": False,
                "fetch_metrics": True,
                "sync_metrics": True,
                "validate_connection": True,
            },
        )
    
    app.include_router(api_router)

    @app.post("/connectors/yandex/sync_metrics", deprecated=True)
    def sync_metrics_alias(payload: YandexSyncMetricsRequest):
        result = sync_yandex_metrics.delay(payload.date_from.date().isoformat(), payload.date_to.date().isoformat())
        return {"job_id": result.id}

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": "http_error",
                    "message": str(exc.detail),
                    "details": {},
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "Validation failed",
                    "details": jsonable_encoder(exc.errors()),
                }
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "Internal server error",
                    "details": {},
                }
            },
        )
    return app


app = create_app()
