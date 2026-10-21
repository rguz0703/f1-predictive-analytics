"""Project configuration.

Settings are read from a TOML file (``configs/default.toml`` by default) and can
be overridden by environment variables. All paths are resolved to absolute
``pathlib.Path`` objects so no other module needs to know where the repository
lives.

The package is intended to be used from a source checkout (``uv sync`` installs
it in editable mode), which is what makes :data:`PROJECT_ROOT` meaningful.

Environment overrides:

``F1PA_DATA_DIR``    data directory
``FASTF1_CACHE``     FastF1 cache directory (same variable FastF1 itself reads)
``F1PA_LOG_LEVEL``   logging level
``F1PA_LOG_FORMAT``  ``text`` or ``json``
"""

from __future__ import annotations

import os
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH: Path = PROJECT_ROOT / "configs" / "default.toml"

#: First season of the Formula 1 World Championship.
EARLIEST_SEASON = 1950
VALID_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})
VALID_LOG_FORMATS = frozenset({"text", "json"})


class ConfigError(ValueError):
    """Raised when the configuration file or an override is missing or invalid."""


@dataclass(frozen=True)
class PathSettings:
    """Absolute filesystem locations used by the pipeline."""

    data_dir: Path
    fastf1_cache_dir: Path

    @property
    def raw_dir(self) -> Path:
        """Unmodified source data, as retrieved."""
        return self.data_dir / "raw"

    @property
    def interim_dir(self) -> Path:
        """Cleaned/validated intermediate tables."""
        return self.data_dir / "interim"

    @property
    def processed_dir(self) -> Path:
        """Model-ready feature tables."""
        return self.data_dir / "processed"


@dataclass(frozen=True)
class DataSettings:
    """Which seasons the ingestion pipeline covers (inclusive range)."""

    first_season: int
    last_season: int

    @property
    def seasons(self) -> list[int]:
        """All seasons from ``first_season`` to ``last_season`` inclusive."""
        return list(range(self.first_season, self.last_season + 1))


@dataclass(frozen=True)
class LoggingSettings:
    """Logging level and output format."""

    level: str
    format: str


@dataclass(frozen=True)
class Settings:
    """Complete, validated project configuration."""

    paths: PathSettings
    data: DataSettings
    logging: LoggingSettings


def load_settings(
    config_path: Path | None = None,
    *,
    env: Mapping[str, str] | None = None,
    project_root: Path = PROJECT_ROOT,
) -> Settings:
    """Load and validate settings.

    Args:
        config_path: TOML file to read. Defaults to ``configs/default.toml``.
        env: Environment mapping used for overrides. Defaults to ``os.environ``;
            pass an explicit mapping in tests for isolation.
        project_root: Base for relative paths in the config file.

    Returns:
        A frozen :class:`Settings` instance with absolute paths.

    Raises:
        ConfigError: If the file is missing, malformed, or contains invalid values.
    """
    config_path = Path(config_path) if config_path is not None else DEFAULT_CONFIG_PATH
    env = os.environ if env is None else env
    raw = _read_toml(config_path)

    paths_cfg = _section(raw, "paths")
    data_cfg = _section(raw, "data")
    log_cfg = _section(raw, "logging")

    data_dir = _resolve(
        env.get("F1PA_DATA_DIR") or _require(paths_cfg, "paths", "data_dir", str), project_root
    )
    cache_dir = _resolve(
        env.get("FASTF1_CACHE") or _require(paths_cfg, "paths", "fastf1_cache_dir", str), data_dir
    )

    first = _require(data_cfg, "data", "first_season", int)
    last = _require(data_cfg, "data", "last_season", int)
    if first < EARLIEST_SEASON:
        raise ConfigError(f"data.first_season={first} is before {EARLIEST_SEASON}")
    if first > last:
        raise ConfigError(f"data.first_season={first} is after data.last_season={last}")

    level = (env.get("F1PA_LOG_LEVEL") or _require(log_cfg, "logging", "level", str)).upper()
    fmt = (env.get("F1PA_LOG_FORMAT") or _require(log_cfg, "logging", "format", str)).lower()
    if level not in VALID_LOG_LEVELS:
        raise ConfigError(
            f"Invalid log level {level!r}; expected one of {sorted(VALID_LOG_LEVELS)}"
        )
    if fmt not in VALID_LOG_FORMATS:
        raise ConfigError(
            f"Invalid log format {fmt!r}; expected one of {sorted(VALID_LOG_FORMATS)}"
        )

    return Settings(
        paths=PathSettings(data_dir=data_dir, fastf1_cache_dir=cache_dir),
        data=DataSettings(first_season=first, last_season=last),
        logging=LoggingSettings(level=level, format=fmt),
    )


def _read_toml(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as fh:
            return tomllib.load(fh)
    except FileNotFoundError as exc:
        raise ConfigError(f"Config file not found: {path}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"Invalid TOML in {path}: {exc}") from exc


def _section(raw: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    value = raw.get(name)
    if not isinstance(value, Mapping):
        raise ConfigError(f"Missing or invalid [{name}] section in config")
    return value


def _require[T](section: Mapping[str, Any], section_name: str, key: str, kind: type[T]) -> T:
    if key not in section:
        raise ConfigError(f"Missing required config key {section_name}.{key}")
    value = section[key]
    # bool is a subclass of int; reject it explicitly for integer fields.
    if not isinstance(value, kind) or (kind is int and isinstance(value, bool)):
        raise ConfigError(
            f"{section_name}.{key} must be {kind.__name__}, got {type(value).__name__}"
        )
    return value


def _resolve(value: str, base: Path) -> Path:
    path = Path(value).expanduser()
    return (path if path.is_absolute() else base / path).resolve()
