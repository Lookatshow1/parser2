import logging
import sys
import structlog
from app.core.context import get_correlation_id

def configure_logging() -> None:
    # Configure standard logging to use structlog
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=logging.INFO)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            add_correlation_id,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

def add_correlation_id(logger, method_name, event_dict):
    correlation_id = get_correlation_id()
    if correlation_id:
        event_dict["correlation_id"] = correlation_id
    return event_dict

def get_logger(name: str):
    return structlog.get_logger(name)
