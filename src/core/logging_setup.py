from __future__ import annotations

import logging
import os

from src.core.trace import TraceFilter


def configure_logging() -> None:
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    root = logging.getLogger()
    root.setLevel(level)

    for handler in root.handlers:
        handler.addFilter(TraceFilter())
        handler.setLevel(level)

    # Uvicorn may have installed handlers already. If it has not, add one.
    if not root.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(level)
        handler.addFilter(TraceFilter())
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-8s | trace=%(trace_id)s | %(name)s | %(message)s",
            datefmt="%H:%M:%S",
        ))
        root.addHandler(handler)

    logging.getLogger("httpx").setLevel(logging.WARNING if level < logging.DEBUG else logging.DEBUG)
    logging.getLogger("websockets").setLevel(logging.WARNING if level < logging.DEBUG else logging.DEBUG)
