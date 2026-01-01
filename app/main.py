from fastapi import FastAPI

from app.api.connections import router as connections_router
from app.api.connectors import router as connectors_router
from app.api.compliance import router as compliance_router
from app.api.events import router as events_router
from app.api.experiments import router as experiments_router
from app.api.health import router as health_router
from app.api.integrations import router as integrations_router
from app.api.plans import router as plans_router
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="Ads Aggregator API")
    app.include_router(health_router)
    app.include_router(connections_router)
    app.include_router(connectors_router)
    app.include_router(compliance_router)
    app.include_router(events_router)
    app.include_router(experiments_router)
    app.include_router(integrations_router)
    app.include_router(plans_router)
    return app


app = create_app()
