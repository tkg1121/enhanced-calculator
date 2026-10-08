from pathlib import Path

import pandas as pd
import pytest

from app.calculation import Calculation
from app.exceptions import HistoryError
from app.history import AutoSaveObserver, History, LoggingObserver


@pytest.mark.parametrize("records", [[], [("add", 2, 3)], [("root", -8, 3), ("divide", 1, 3)]])
def test_csv_roundtrip(tmp_path, records):
    history = History()
    for values in records:
        history.append(Calculation.create(*values))
    path = tmp_path / "nested" / "history.csv"
    history.save(path)
    loaded = History()
    loaded.load(path)
    assert loaded.frame.to_dict("records") == history.frame.to_dict("records")
    history.clear()
    assert history.frame.empty
    assert list(history.frame.columns) == History.columns


@pytest.mark.parametrize("content", [
    "", "bad,columns\n1,2\n", 'operation,first,second,result\n"unterminated',
    "operation,first,second,result\nadd,1,2,99\n",
    "operation,first,second,result\nadd,nan,2,3\n",
    "operation,first,second,result\nadd,1,inf,3\n",
    "operation,first,second,result\nadd,1,2,nan\n",
    "operation,first,second,result\nunknown,1,2,3\n",
    "operation,first,second,result\ndivide,1,0,0\n",
    "operation,first,second,result\nadd,1,2,3\nadd,broken,2,3\n",
])
def test_corrupt_csv_preserves_existing_history(tmp_path, content):
    history = History()
    history.append(Calculation.create("add", 4, 5))
    before = history.frame.copy(deep=True)
    path = tmp_path / "bad.csv"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(HistoryError):
        history.load(path)
    pd.testing.assert_frame_equal(history.frame, before)


def test_missing_history(tmp_path):
    with pytest.raises(HistoryError, match="load"):
        History().load(tmp_path / "missing.csv")


@pytest.mark.parametrize("failure", ["mkdir", "to_csv", "replace"])
def test_save_failure_preserves_old_file(monkeypatch, tmp_path, failure):
    path = tmp_path / "history.csv"
    original = "operation,first,second,result\nadd,1,2,3\n"
    path.write_text(original, encoding="utf-8")

    def denied(*args, **kwargs):
        raise PermissionError("denied")

    if failure == "mkdir":
        monkeypatch.setattr(Path, "mkdir", denied)
    elif failure == "to_csv":
        monkeypatch.setattr(pd.DataFrame, "to_csv", denied)
    else:
        monkeypatch.setattr("app.history.os.replace", denied)
    with pytest.raises(HistoryError, match="save"):
        History().save(path)
    assert path.read_text(encoding="utf-8") == original
    assert list(tmp_path.iterdir()) == [path]


@pytest.mark.parametrize("event", ["calculate", "clear", "undo", "redo", "load"])
def test_observers_write_current_history(tmp_path, event):
    history = History()
    history.append(Calculation.create("add", 2, 3))
    log = tmp_path / "logs" / "events.log"
    saved = tmp_path / "history.csv"
    LoggingObserver(log).update(event, history)
    AutoSaveObserver(saved).update(event, history)
    assert log.read_text(encoding="utf-8") == f"{event}: 1 calculation(s)\n"
    assert pd.read_csv(saved)["result"].tolist() == [5]
