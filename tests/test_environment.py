"""Offline checks that the installed environment matches the documented constraints."""

from __future__ import annotations

import sys

import f1_predictive_analytics


def test_python_version_is_supported() -> None:
    assert sys.version_info[:2] == (3, 12)


def test_package_version_is_resolved_from_metadata() -> None:
    assert f1_predictive_analytics.__version__ != "0.0.0+unknown"


def test_core_dependencies_import_with_compatible_versions() -> None:
    import fastf1
    import numpy
    import pandas

    # FastF1 3.8 is not compatible with pandas/numpy 3.
    assert int(pandas.__version__.split(".")[0]) == 2
    assert int(numpy.__version__.split(".")[0]) <= 2
    assert int(fastf1.__version__.split(".")[0]) == 3
