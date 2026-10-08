import pytest

from app.exceptions import ValidationError
from app.input_validators import validate_number


@pytest.mark.parametrize("value, expected", [(2, 2), ("10", 10), (" -2.5 ", -2.5), ("1e2", 100), (0, 0)])
def test_valid_numbers(value, expected):
    assert validate_number(value) == expected


@pytest.mark.parametrize("value", ["", "two", "1 2", "3,4", None, [], 10**1000])
def test_invalid_numbers(value):
    with pytest.raises(ValidationError, match="Enter a number"):
        validate_number(value)


@pytest.mark.parametrize("value", ["nan", "NaN", "inf", "-inf", "+Infinity", "1e999", float("nan"), float("inf")])
def test_nonfinite_numbers_are_rejected(value):
    with pytest.raises(ValidationError, match="finite"):
        validate_number(value)
