import pytest

from app.exceptions import OperationError, ValidationError
from app.operations import Add, Operation, OperationFactory


@pytest.mark.parametrize("name, first, second, expected", [
    ("add", 2, 3, 5), ("add", -2, -3, -5), ("add", .1, .2, .3),
    ("subtract", 2, 5, -3), ("subtract", -2, -5, 3),
    ("multiply", -2, 3, -6), ("multiply", 0, 4, 0), ("multiply", .5, .5, .25),
    ("divide", 9, 2, 4.5), ("divide", -4, 2, -2), ("divide", 0, 2, 0),
    ("power", 2, 3, 8), ("power", 4, .5, 2), ("power", 2, -2, .25),
    ("power", -2, 3, -8), ("power", 0, 0, 1),
    ("root", 27, 3, 3), ("root", -27, 3, -3), ("root", 16, 2, 4),
    ("root", 16, -2, .25), ("root", -8, -3, -.5), ("root", 9, .5, 81),
    ("root", 0, 2, 0), (" ADD ", 1, 2, 3),
])
def test_strategies(name, first, second, expected):
    assert OperationFactory.create(name).execute(first, second) == pytest.approx(expected)


@pytest.mark.parametrize("name, first, second", [
    ("divide", 1, 0), ("divide", 0, -0.0), ("root", 3, 0),
    ("root", -4, 2), ("root", -4, 2.5), ("root", 0, -2),
    ("power", -2, .5), ("power", 0, -1), ("power", 1e308, 2),
    ("multiply", 1e308, 2), ("add", 1e308, 1e308),
    ("root", 1e308, .01),
])
def test_domain_and_overflow_errors(name, first, second):
    with pytest.raises(OperationError):
        OperationFactory.create(name).execute(first, second)


@pytest.mark.parametrize("name", ["", "+", "unknown"])
def test_invalid_operation(name):
    with pytest.raises(OperationError, match="Choose"):
        OperationFactory.create(name)


@pytest.mark.parametrize("first, second", [("nan", 1), (1, "inf"), (None, 2)])
def test_strategy_validates_operands(first, second):
    with pytest.raises(ValidationError):
        Add().execute(first, second)


def test_strategy_is_interchangeable(monkeypatch):
    class Maximum(Operation):
        def _calculate(self, first, second):
            return max(first, second)

    monkeypatch.setitem(OperationFactory.strategies, "maximum", Maximum)
    assert OperationFactory.create("maximum").execute(2, 7) == 7


def test_base_strategy_requires_implementation():
    with pytest.raises(TypeError):
        Operation()
