from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.connections import router as connections_router
from app.api.connectors import router as connectors_router
from app.api.compliance import router as compliance_router
from app.api.events import router as events_router
from app.api.experiments import router as experiments_router
from app.api.health import router as health_router
from app.api.integrations import router as integrations_router
from app.api.plans import router as plans_router
from app.api.schemas import ApiCapabilitiesResponse, ApiVersionResponse
from app.core.config import get_settings
from app.core.logging import configure_logging


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
    app.include_router(connections_router)
    app.include_router(connectors_router)
    app.include_router(compliance_router)
    app.include_router(events_router)
    app.include_router(experiments_router)
    app.include_router(integrations_router)
    app.include_router(plans_router)

    @app.get("/api/version", response_model=ApiVersionResponse)
    def api_version():
        return ApiVersionResponse(version="0.1.0")

    @app.get("/api/capabilities", response_model=ApiCapabilitiesResponse)
    def api_capabilities():
        return ApiCapabilitiesResponse(
            platforms=["yandex", "ozon", "vk"],
            operations={
                "create_campaign": False,
                "fetch_metrics": True,
                "sync_metrics": True,
                "validate_connection": True,
            },
        )

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
                    "details": exc.errors(),
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
