"""Structured logging configuration.

Modules log with ``logging.getLogger(__name__)`` and pass context through
``extra``, for example::

    logger.info("session loaded", extra={"season": 2024, "round": 1, "rows": 20})

Entry points call :func:`configure_logging` once. Two formats are supported:

* ``text``: ``2026-10-20T19:00:00.000Z INFO module: session loaded season=2024 round=1``
* ``json``: one JSON object per line, suitable for log aggregation.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any, TextIO

from f1_predictive_analytics.config import VALID_LOG_FORMATS, VALID_LOG_LEVELS

# Attributes present on every LogRecord; anything else came from ``extra``.
_STANDARD_ATTRS = frozenset(vars(logging.makeLogRecord({}))) | {"message", "asctime", "taskName"}
_HANDLER_MARKER = "_f1pa_handler"


def _extra_fields(record: logging.LogRecord) -> dict[str, Any]:
    return {
        k: v for k, v in vars(record).items() if k not in _STANDARD_ATTRS and not k.startswith("_")
    }


def _timestamp(record: logging.LogRecord) -> str:
    ts = datetime.fromtimestamp(record.created, tz=UTC).isoformat(timespec="milliseconds")
    return ts.replace("+00:00", "Z")


class JsonFormatter(logging.Formatter):
    """Format records as single-line JSON objects including ``extra`` fields."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": _timestamp(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            **_extra_fields(record),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str, ensure_ascii=False)


class KeyValueFormatter(logging.Formatter):
    """Human-readable format with ``extra`` fields appended as ``key=value``."""

    def format(self, record: logging.LogRecord) -> str:
        line = f"{_timestamp(record)} {record.levelname} {record.name}: {record.getMessage()}"
        extras = " ".join(f"{k}={v}" for k, v in _extra_fields(record).items())
        if extras:
            line = f"{line} {extras}"
        if record.exc_info:
            line = f"{line}\n{self.formatException(record.exc_info)}"
        return line


def configure_logging(level: str = "INFO", fmt: str = "text", stream: TextIO | None = None) -> None:
    """Configure the root logger. Safe to call more than once.

    Args:
        level: Logging level name (e.g. ``"INFO"``).
        fmt: ``"text"`` or ``"json"``.
        stream: Output stream; defaults to ``sys.stderr``.

    Raises:
        ValueError: If ``level`` or ``fmt`` is not recognised.
    """
    level = level.upper()
    if level not in VALID_LOG_LEVELS:
        raise ValueError(f"Invalid log level {level!r}")
    if fmt not in VALID_LOG_FORMATS:
        raise ValueError(f"Invalid log format {fmt!r}")

    handler = logging.StreamHandler(stream or sys.stderr)
    handler.setFormatter(JsonFormatter() if fmt == "json" else KeyValueFormatter())
    setattr(handler, _HANDLER_MARKER, True)

    root = logging.getLogger()
    # Replace only handlers installed by this function; leave others (e.g. pytest's) alone.
    for existing in [h for h in root.handlers if getattr(h, _HANDLER_MARKER, False)]:
        root.removeHandler(existing)
    root.addHandler(handler)
    root.setLevel(level)
