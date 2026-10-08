"""DataFrame history, validated CSV storage, and event observers."""

from dataclasses import asdict
import math
import os
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from app.calculation import Calculation
from app.exceptions import CalculatorError, HistoryError
from app.input_validators import validate_number


class History:
    """Store calculation records and exchange them with CSV files."""

    columns = ["operation", "first", "second", "result"]

    def __init__(self):
        self.frame = pd.DataFrame(columns=self.columns)

    def append(self, calculation: Calculation):
        self.frame.loc[len(self.frame)] = asdict(calculation)

    def clear(self):
        self.frame = pd.DataFrame(columns=self.columns)

    def save(self, path: Path):
        """Replace the destination only after a complete CSV has been written."""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with TemporaryDirectory(dir=path.parent) as folder:
                temporary = Path(folder) / "history.csv"
                self.frame.to_csv(temporary, index=False)
                os.replace(temporary, path)
        except OSError as error:
            raise HistoryError(f"Could not save history: {error}") from error

    def load(self, path: Path):
        """Validate every row before replacing the in-memory history."""
        try:
            frame = pd.read_csv(path, dtype=str, keep_default_na=False)
            if list(frame.columns) != self.columns:
                raise HistoryError("CSV columns must be operation, first, second, result.")
            loaded = History()
            for row in frame.itertuples(index=False):
                calculation = Calculation.create(row.operation, row.first, row.second)
                result = validate_number(row.result)
                if not math.isclose(result, calculation.result, rel_tol=1e-12, abs_tol=1e-12):
                    raise HistoryError("A saved result does not match its calculation.")
                loaded.append(calculation)
        except (OSError, ValueError, CalculatorError) as error:
            raise HistoryError(f"Could not load history: {error}") from error
        self.frame = loaded.frame


class LoggingObserver:
    """Append a short local event log whenever history changes."""

    def __init__(self, path: Path):
        self.path = path

    def update(self, event: str, history: History):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(f"{event}: {len(history.frame)} calculation(s)\n")


class AutoSaveObserver:
    """Persist the current history after each state change."""

    def __init__(self, path: Path):
        self.path = path

    def update(self, event: str, history: History):
        history.save(self.path)
