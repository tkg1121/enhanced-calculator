import pytest

from app.calculator_config import CalculatorConfig


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    for name in ("HISTORY_FILE", "LOG_FILE", "AUTOSAVE", "PRECISION"):
        monkeypatch.delenv(f"CALCULATOR_{name}", raising=False)


@pytest.fixture
def config(tmp_path):
    return CalculatorConfig(tmp_path / "history.csv", tmp_path / "calculator.log")


@pytest.fixture
def inputs(monkeypatch):
    def install(values):
        entries = iter(values)

        def fake_input(prompt):
            entry = next(entries)
            if isinstance(entry, BaseException):
                raise entry
            return entry

        monkeypatch.setattr("builtins.input", fake_input)

    return install
