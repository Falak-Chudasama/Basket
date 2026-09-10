from __future__ import annotations

import contextvars
import logging
from contextlib import contextmanager
from uuid import uuid4

_trace_id: contextvars.ContextVar[str] = contextvars.ContextVar("trace_id", default="-")


def new_trace_id() -> str:
    return uuid4().hex[:10]


def get_trace_id() -> str:
    return _trace_id.get()


def set_trace_id(trace_id: str):
    return _trace_id.set(trace_id)


def reset_trace_id(token) -> None:
    _trace_id.reset(token)


@contextmanager
def trace_scope(trace_id: str | None = None):
    token = set_trace_id(trace_id or new_trace_id())
    try:
        yield get_trace_id()
    finally:
        reset_trace_id(token)


class TraceFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = get_trace_id()
        return True
