import pandas as pd
import pytest

from app.calculator_memento import CalculatorMemento, UndoRedo
from app.exceptions import StateError


@pytest.mark.parametrize("values", [[], [1], [1, 2]])
def test_snapshot_is_independent(values):
    frame = pd.DataFrame({"value": values})
    snapshot = CalculatorMemento.capture(frame)
    frame.loc[len(frame)] = 99
    restored = snapshot.restore()
    assert restored["value"].tolist() == values
    restored.loc[len(restored)] = 88
    assert snapshot.restore()["value"].tolist() == values


@pytest.mark.parametrize("action", ["undo", "redo"])
def test_empty_stacks(action):
    with pytest.raises(StateError, match="Nothing"):
        getattr(UndoRedo(), action)(pd.DataFrame())


def test_multiple_undo_redo_and_new_branch():
    states = UndoRedo()
    empty = pd.DataFrame({"value": []})
    one = pd.DataFrame({"value": [1]})
    two = pd.DataFrame({"value": [1, 2]})
    states.record(empty)
    states.record(one)
    restored_one = states.undo(two)
    assert restored_one.equals(one)
    restored_empty = states.undo(restored_one)
    assert restored_empty["value"].empty
    assert states.redo(restored_empty).equals(one)
    assert states.redo(one).equals(two)
    states.undo(two)
    states.record(one)
    with pytest.raises(StateError):
        states.redo(one)
