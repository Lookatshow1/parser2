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
from app.api.builder import router as builder_router
from app.api.catalog import router as catalog_router
from app.api.automation import router as automation_router
from app.api.campaigns import campaigns_router, ad_groups_router, ads_router
from app.api.recommendations import router as recommendations_router
from app.api.change_plans import router as change_plans_router
from app.api.studio import router as studio_router
from app.api.platforms import router as platforms_router
from app.api.settings import router as settings_router
from app.api.magic import router as magic_router
from app.api.drafts import router as drafts_router
from app.api.billing import router as billing_router
from app.api.abtests import router as abtests_router
from app.api.admin import router as admin_router
from app.api.ai_endpoints import router as ai_router
from app.api.metrica import router as metrica_router
from app.api.telegram import router as telegram_router
from app.api.templates import router as templates_router
from app.api.payments import router as payments_router
from app.api.magic_launch import router as magic_launch_router




from app.api.schemas import ApiCapabilitiesResponse, ApiVersionResponse, HealthResponse, YandexSyncMetricsRequest
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.workers.yandex_tasks import sync_yandex_metrics
from app.middleware.correlation import CorrelationIdMiddleware


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="Ads Aggregator API")
    settings = get_settings()
    origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]

    # Add middlewares
    app.add_middleware(CorrelationIdMiddleware)
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
    api_router.include_router(builder_router)
    api_router.include_router(campaigns_router)
    api_router.include_router(ad_groups_router)
    api_router.include_router(ads_router)
    api_router.include_router(catalog_router)
    api_router.include_router(recommendations_router)
    api_router.include_router(change_plans_router)
    api_router.include_router(studio_router)
    api_router.include_router(automation_router)
    api_router.include_router(platforms_router)
    api_router.include_router(settings_router)
    api_router.include_router(magic_router)
    api_router.include_router(drafts_router)
    api_router.include_router(billing_router)
    api_router.include_router(abtests_router)
    api_router.include_router(admin_router)
    api_router.include_router(ai_router)
    api_router.include_router(metrica_router)
    api_router.include_router(telegram_router)
    api_router.include_router(templates_router)
    api_router.include_router(payments_router)
    api_router.include_router(magic_launch_router)





    @api_router.get("/version", response_model=ApiVersionResponse)
    def api_version():
        return ApiVersionResponse(version="0.1.0")

    @api_router.get("/capabilities", response_model=ApiCapabilitiesResponse)
    def api_capabilities():
        return ApiCapabilitiesResponse(
            platforms=["yandex", "ozon", "vk", "stub"],
            operations={
                "create_campaign": True,
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
