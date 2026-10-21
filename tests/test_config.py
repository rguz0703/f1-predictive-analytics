"""Tests for configuration loading, validation and environment overrides."""

from __future__ import annotations

from pathlib import Path

import pytest

from f1_predictive_analytics.config import (
    DEFAULT_CONFIG_PATH,
    PROJECT_ROOT,
    ConfigError,
    load_settings,
)

VALID_TOML = """
[paths]
data_dir = "data"
fastf1_cache_dir = "cache/fastf1"

[data]
first_season = 2018
last_season = 2020

[logging]
level = "info"
format = "text"
"""


def write_config(tmp_path: Path, text: str = VALID_TOML) -> Path:
    path = tmp_path / "config.toml"
    path.write_text(text, encoding="utf-8")
    return path


def test_default_config_file_loads() -> None:
    settings = load_settings(env={})
    assert DEFAULT_CONFIG_PATH.is_file()
    assert settings.paths.data_dir == PROJECT_ROOT / "data"
    assert settings.paths.fastf1_cache_dir == PROJECT_ROOT / "data" / "cache" / "fastf1"
    assert settings.data.first_season <= settings.data.last_season


def test_relative_paths_resolve_against_root_and_data_dir(tmp_path: Path) -> None:
    settings = load_settings(write_config(tmp_path), env={}, project_root=tmp_path)
    assert settings.paths.data_dir == tmp_path.resolve() / "data"
    assert settings.paths.fastf1_cache_dir == tmp_path.resolve() / "data" / "cache" / "fastf1"
    assert settings.paths.raw_dir == settings.paths.data_dir / "raw"
    assert settings.paths.processed_dir == settings.paths.data_dir / "processed"


def test_seasons_range_is_inclusive(tmp_path: Path) -> None:
    settings = load_settings(write_config(tmp_path), env={}, project_root=tmp_path)
    assert settings.data.seasons == [2018, 2019, 2020]


def test_log_level_is_normalised(tmp_path: Path) -> None:
    settings = load_settings(write_config(tmp_path), env={}, project_root=tmp_path)
    assert settings.logging.level == "INFO"


def test_environment_overrides(tmp_path: Path) -> None:
    env = {
        "F1PA_DATA_DIR": str(tmp_path / "elsewhere"),
        "FASTF1_CACHE": str(tmp_path / "f1cache"),
        "F1PA_LOG_LEVEL": "debug",
        "F1PA_LOG_FORMAT": "JSON",
    }
    settings = load_settings(write_config(tmp_path), env=env, project_root=tmp_path)
    assert settings.paths.data_dir == (tmp_path / "elsewhere").resolve()
    assert settings.paths.fastf1_cache_dir == (tmp_path / "f1cache").resolve()
    assert settings.logging.level == "DEBUG"
    assert settings.logging.format == "json"


def test_empty_env_value_does_not_override(tmp_path: Path) -> None:
    settings = load_settings(
        write_config(tmp_path), env={"F1PA_DATA_DIR": ""}, project_root=tmp_path
    )
    assert settings.paths.data_dir == tmp_path.resolve() / "data"


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="not found"):
        load_settings(tmp_path / "nope.toml", env={})


def test_malformed_toml_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="Invalid TOML"):
        load_settings(write_config(tmp_path, "[paths\n"), env={})


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ("last_season = 2020", "last_season = 2010", "after"),
        ("first_season = 2018", "first_season = 1949", "before 1950"),
        ("first_season = 2018", 'first_season = "2018"', "must be int"),
        ("first_season = 2018", "first_season = true", "must be int"),
        ("first_season = 2018\n", "", "data.first_season"),
        ('level = "info"', 'level = "loud"', "Invalid log level"),
        ('format = "text"', 'format = "xml"', "Invalid log format"),
        ("[logging]", "[other]", r"\[logging\]"),
    ],
)
def test_invalid_values_raise(tmp_path: Path, old: str, new: str, message: str) -> None:
    assert old in VALID_TOML
    path = write_config(tmp_path, VALID_TOML.replace(old, new))
    with pytest.raises(ConfigError, match=message):
        load_settings(path, env={}, project_root=tmp_path)
