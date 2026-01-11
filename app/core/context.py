import contextvars
import uuid

_correlation_id_ctx_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "correlation_id", default=None
)

def get_correlation_id() -> str:
    val = _correlation_id_ctx_var.get()
    if not val:
        val = str(uuid.uuid4())
        _correlation_id_ctx_var.set(val)
    return val

def set_correlation_id(val: str) -> None:
    _correlation_id_ctx_var.set(val)
