from pathlib import Path

import pytest

from app.calculator_config import CalculatorConfig
from app.exceptions import ConfigurationError


def test_default_settings():
    config = CalculatorConfig.from_env()
    assert config.history_file == Path("data/history.csv")
    assert config.log_file == Path("data/calculator.log")
    assert config.autosave is True
    assert config.precision == 10


@pytest.mark.parametrize("value, expected", [("true", True), ("false", False), (" TRUE ", True)])
def test_autosave_environment(monkeypatch, value, expected):
    monkeypatch.setenv("CALCULATOR_AUTOSAVE", value)
    assert CalculatorConfig.from_env().autosave is expected


@pytest.mark.parametrize("key, value", [
    ("AUTOSAVE", "yes"), ("PRECISION", "words"), ("PRECISION", "0"),
    ("PRECISION", "18"), ("HISTORY_FILE", " "), ("LOG_FILE", ""),
])
def test_invalid_environment(monkeypatch, key, value):
    monkeypatch.setenv(f"CALCULATOR_{key}", value)
    with pytest.raises(ConfigurationError):
        CalculatorConfig.from_env()


@pytest.mark.parametrize("precision", [1, 17])
def test_precision_boundaries(precision):
    assert CalculatorConfig(precision=precision).precision == precision


@pytest.mark.parametrize("options", [{"precision": True}, {"precision": 1.5}, {"autosave": "false"}])
def test_direct_invalid_settings(options):
    with pytest.raises(ConfigurationError):
        CalculatorConfig(**options)


def test_env_file_and_environment_precedence(monkeypatch, tmp_path):
    env = tmp_path / ".env"
    env.write_text("CALCULATOR_PRECISION=5\nCALCULATOR_AUTOSAVE=false\nCALCULATOR_HISTORY_FILE=other.csv\n", encoding="utf-8")
    monkeypatch.setenv("CALCULATOR_PRECISION", "7")
    config = CalculatorConfig.from_env(env)
    assert config.precision == 7
    assert config.autosave is False
    assert config.history_file == Path("other.csv")


def test_conflicting_paths(tmp_path):
    path = tmp_path / "same.csv"
    with pytest.raises(ConfigurationError, match="different"):
        CalculatorConfig(path, path)


@pytest.mark.parametrize("field", ["history_file", "log_file"])
def test_directory_is_not_a_file(tmp_path, field):
    with pytest.raises(ConfigurationError, match="directory"):
        CalculatorConfig(**{field: tmp_path})


def test_unreadable_env(monkeypatch):
    def denied(*args, **kwargs):
        raise PermissionError("denied")

    monkeypatch.setattr("app.calculator_config.load_dotenv", denied)
    with pytest.raises(ConfigurationError, match="denied"):
        CalculatorConfig.from_env()
