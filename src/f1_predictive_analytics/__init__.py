"""F1 Predictive Analytics Platform.

Reproducible Formula 1 data pipeline and predictive models. See README.md for
the current implementation status; modules are added milestone by milestone.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("f1-predictive-analytics")
except PackageNotFoundError:  # running from a source tree without installation
    __version__ = "0.0.0+unknown"

__all__ = ["__version__"]
