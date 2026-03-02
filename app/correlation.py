import uuid
from contextvars import ContextVar
from typing import Optional

import structlog

_correlation_id_ctx_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


def get_correlation_id() -> str:
    try:
        context = structlog.contextvars.get_contextvars()
        if 'correlation_id' in context:
            return context['correlation_id']
    except:
        pass

    correlation_id = _correlation_id_ctx_var.get()
    if correlation_id:
        return correlation_id

    return str(uuid.uuid4())


def set_correlation_id(correlation_id: str) -> None:
    _correlation_id_ctx_var.set(correlation_id)
    structlog.contextvars.bind_contextvars(correlation_id=correlation_id)
