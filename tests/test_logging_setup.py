"""Tests for structured logging configuration."""

from __future__ import annotations

import io
import json
import logging
from collections.abc import Iterator

import pytest

from f1_predictive_analytics.utils.logging_setup import configure_logging


@pytest.fixture(autouse=True)
def restore_root_logger() -> Iterator[None]:
    root = logging.getLogger()
    handlers, level = list(root.handlers), root.level
    yield
    root.handlers[:] = handlers
    root.setLevel(level)


def test_json_format_includes_extra_fields() -> None:
    stream = io.StringIO()
    configure_logging("INFO", "json", stream=stream)
    logging.getLogger("f1pa.test").info("loaded", extra={"season": 2024, "rows": 20})

    record = json.loads(stream.getvalue().strip())
    assert record["message"] == "loaded"
    assert record["level"] == "INFO"
    assert record["logger"] == "f1pa.test"
    assert record["season"] == 2024
    assert record["rows"] == 20
    assert record["timestamp"].endswith("Z")


def test_text_format_appends_key_values() -> None:
    stream = io.StringIO()
    configure_logging("INFO", "text", stream=stream)
    logging.getLogger("f1pa.test").warning("missing laps", extra={"driver": "VER"})

    line = stream.getvalue().strip()
    assert "WARNING f1pa.test: missing laps" in line
    assert line.endswith("driver=VER")


def test_level_filters_records() -> None:
    stream = io.StringIO()
    configure_logging("WARNING", "text", stream=stream)
    logging.getLogger("f1pa.test").info("hidden")
    assert stream.getvalue() == ""


def test_reconfiguring_does_not_duplicate_handlers() -> None:
    first, second = io.StringIO(), io.StringIO()
    configure_logging("INFO", "text", stream=first)
    configure_logging("INFO", "text", stream=second)
    logging.getLogger("f1pa.test").info("once")

    assert first.getvalue() == ""
    assert second.getvalue().count("once") == 1


def test_exceptions_are_serialised_in_json() -> None:
    stream = io.StringIO()
    configure_logging("INFO", "json", stream=stream)
    try:
        raise RuntimeError("boom")
    except RuntimeError:
        logging.getLogger("f1pa.test").exception("failed")

    record = json.loads(stream.getvalue().strip())
    assert "RuntimeError: boom" in record["exception"]


@pytest.mark.parametrize(("level", "fmt"), [("LOUD", "text"), ("INFO", "xml")])
def test_invalid_arguments_raise(level: str, fmt: str) -> None:
    with pytest.raises(ValueError):
        configure_logging(level, fmt)
