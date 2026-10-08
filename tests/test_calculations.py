from dataclasses import FrozenInstanceError

import pytest

from app.calculation import Calculation
from app.exceptions import CalculatorError


@pytest.mark.parametrize("name, first, second, expected", [(" ADD ", "2", "3", 5), ("root", "-8", "3", -2), ("power", "2", "-2", .25)])
def test_calculation_record(name, first, second, expected):
    result = Calculation.create(name, first, second)
    assert result.operation == name.strip().lower()
    assert result.first == float(first)
    assert result.second == float(second)
    assert result.result == pytest.approx(expected)
    with pytest.raises(FrozenInstanceError):
        result.result = 99


@pytest.mark.parametrize("name, first, second", [("bad", 1, 2), ("add", "nan", 1), ("add", 1, "inf"), ("divide", 1, 0)])
def test_invalid_calculation(name, first, second):
    with pytest.raises(CalculatorError):
        Calculation.create(name, first, second)
