"""Independent history snapshots and the undo/redo caretaker."""

from dataclasses import dataclass

import pandas as pd

from app.exceptions import StateError


@dataclass(frozen=True)
class CalculatorMemento:
    """Immutable values copied out of a history DataFrame."""

    columns: tuple
    rows: tuple

    @classmethod
    def capture(cls, frame: pd.DataFrame):
        return cls(tuple(frame.columns), tuple(frame.itertuples(index=False, name=None)))

    def restore(self) -> pd.DataFrame:
        """Build a fresh frame so callers cannot modify the snapshot."""
        return pd.DataFrame(self.rows, columns=self.columns)


class UndoRedo:
    """Keep past and future states for one calculator session."""

    def __init__(self):
        self._undo = []
        self._redo = []

    def record(self, current: pd.DataFrame):
        self._undo.append(CalculatorMemento.capture(current))
        self._redo.clear()

    def undo(self, current: pd.DataFrame) -> pd.DataFrame:
        if not self._undo:
            raise StateError("Nothing to undo.")
        self._redo.append(CalculatorMemento.capture(current))
        return self._undo.pop().restore()

    def redo(self, current: pd.DataFrame) -> pd.DataFrame:
        if not self._redo:
            raise StateError("Nothing to redo.")
        self._undo.append(CalculatorMemento.capture(current))
        return self._redo.pop().restore()
