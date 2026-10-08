from dataclasses import replace
import runpy

import pandas as pd
import pytest

from app.calculator_repl import Calculator, main, run
from app.exceptions import CalculatorError, HistoryError, StateError


def test_facade_persists_and_reloads(config):
    calculator = Calculator(config)
    assert calculator.show_history() == "History is empty."
    calculator.calculate("add", 1, 2)
    calculator.calculate("root", 9, 2)
    assert "add" in calculator.show_history()
    restarted = Calculator(config)
    assert restarted.history.frame["result"].tolist() == [3, 3]
    with pytest.raises(StateError):
        restarted.undo()
    calculator.undo()
    assert pd.read_csv(config.history_file)["operation"].tolist() == ["add"]
    calculator.redo()
    assert len(pd.read_csv(config.history_file)) == 2
    calculator.clear()
    assert pd.read_csv(config.history_file).empty
    calculator.undo()
    assert len(calculator.history.frame) == 2
    calculator.redo()
    assert calculator.history.frame.empty


def test_manual_save_load_is_undoable(config):
    calculator = Calculator(replace(config, autosave=False))
    calculator.calculate("add", 1, 2)
    assert not config.history_file.exists()
    calculator.save()
    calculator.calculate("multiply", 2, 3)
    calculator.load()
    assert calculator.history.frame["result"].tolist() == [3]
    calculator.undo()
    assert calculator.history.frame["result"].tolist() == [3, 6]
    calculator.redo()
    assert calculator.history.frame["result"].tolist() == [3]


@pytest.mark.parametrize("name, first, second", [("divide", 1, 0), ("add", "nan", 2), ("add", 1, "inf")])
def test_failed_calculation_does_not_change_stacks_or_disk(config, name, first, second):
    calculator = Calculator(config)
    calculator.calculate("add", 1, 2)
    calculator.undo()
    before = config.history_file.read_bytes()
    with pytest.raises(CalculatorError):
        calculator.calculate(name, first, second)
    assert calculator.history.frame.empty
    assert config.history_file.read_bytes() == before
    calculator.redo()
    assert calculator.history.frame["result"].tolist() == [3]


def test_failed_load_preserves_state_and_redo(config):
    calculator = Calculator(config)
    calculator.calculate("add", 1, 2)
    calculator.undo()
    config.history_file.write_text("bad\n", encoding="utf-8")
    with pytest.raises(HistoryError):
        calculator.load()
    assert calculator.history.frame.empty
    calculator.redo()
    assert calculator.history.frame["result"].tolist() == [3]


def test_new_calculation_invalidates_redo(config):
    calculator = Calculator(config)
    calculator.calculate("add", 1, 2)
    calculator.undo()
    calculator.calculate("multiply", 3, 4)
    with pytest.raises(StateError):
        calculator.redo()


@pytest.mark.parametrize("error", [OSError("disk full"), HistoryError("save failed")])
def test_observer_failures_allow_remaining_observers(config, error):
    class BrokenObserver:
        def update(self, event, history):
            raise error

    calculator = Calculator(config)
    broken = BrokenObserver()
    calculator.observers.insert(0, broken)
    calculator.subscribe(broken)
    assert calculator.observers.count(broken) == 1
    calculator.calculate("add", 1, 2)
    assert str(error) in calculator.warnings[0]
    assert len(pd.read_csv(config.history_file)) == 1
    assert "calculate" in config.log_file.read_text(encoding="utf-8")


def test_subscribe_custom_observer(config):
    events = []

    class Observer:
        def update(self, event, history):
            events.append((event, len(history.frame)))

    calculator = Calculator(config)
    calculator.subscribe(Observer())
    calculator.calculate("add", 1, 2)
    assert events == [("calculate", 1)]


def test_repl_commands(config, inputs, capsys):
    calculator = Calculator(config)
    inputs(["help", "history", " ADD ", "2", "3", "history", "save", "undo", "redo", "load", "clear", "exit"])
    run(calculator)
    output = capsys.readouterr().out
    for text in ["Operations:", "History is empty.", "Result: 5", "add", "Save complete.", "Undo complete.", "Redo complete.", "Load complete.", "Clear complete.", "Goodbye."]:
        assert text in output


@pytest.mark.parametrize("entries, expected", [
    (["invalid"], "Choose"), (["add", "nan", "2"], "finite"),
    (["add", "1", "inf"], "finite"), (["add", "abc", "2"], "Enter a number"),
    (["divide", "1", "0"], "zero"), (["undo"], "Nothing to undo"),
    (["redo"], "Nothing to redo"), (["load"], "Could not load"),
])
def test_repl_error_recovery(config, inputs, capsys, entries, expected):
    calculator = Calculator(config)
    inputs(entries + ["add", "1", "2", "exit"])
    run(calculator)
    output = capsys.readouterr().out
    assert "Error:" in output
    assert expected in output
    assert "Result: 3" in output
    assert len(calculator.history.frame) == 1


@pytest.mark.parametrize("prefix", [[], ["add"], ["add", "1"]])
@pytest.mark.parametrize("ending", ["exit", " EXIT ", EOFError(), KeyboardInterrupt()])
def test_exit_at_any_prompt(config, inputs, capsys, prefix, ending):
    inputs(prefix + [ending])
    run(Calculator(config))
    assert "Goodbye." in capsys.readouterr().out


def test_autosave_warning_and_retry(config, inputs, capsys, monkeypatch):
    calculator = Calculator(config)
    original = calculator.history.save
    attempts = []

    def fail_once(path):
        attempts.append(path)
        if len(attempts) == 1:
            raise HistoryError("disk full")
        original(path)

    monkeypatch.setattr(calculator.history, "save", fail_once)
    inputs(["add", "1", "2", "save", "exit"])
    run(calculator)
    output = capsys.readouterr().out
    assert "Result: 3" in output
    assert "Warning: AutoSaveObserver: disk full" in output
    assert "Save complete." in output
    assert pd.read_csv(config.history_file)["result"].tolist() == [3]


@pytest.mark.parametrize("failure", ["config", "history"])
def test_startup_failure(monkeypatch, tmp_path, capsys, failure):
    if failure == "config":
        monkeypatch.setenv("CALCULATOR_PRECISION", "invalid")
    else:
        path = tmp_path / "bad.csv"
        path.write_text("bad\n", encoding="utf-8")
        monkeypatch.setenv("CALCULATOR_HISTORY_FILE", str(path))
    assert main() == 1
    assert "Startup error:" in capsys.readouterr().out


def test_module_entrypoint(inputs, capsys):
    inputs(["exit"])
    with pytest.raises(SystemExit) as error:
        runpy.run_module("app", run_name="__main__")
    assert error.value.code == 0
    assert "Goodbye." in capsys.readouterr().out
