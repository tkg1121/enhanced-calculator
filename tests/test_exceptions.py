import pytest

from app.exceptions import CalculatorError, ConfigurationError, HistoryError, OperationError, StateError, ValidationError


@pytest.mark.parametrize("error_type", [CalculatorError, ConfigurationError, HistoryError, OperationError, StateError, ValidationError])
def test_errors_have_a_common_base_and_message(error_type):
    with pytest.raises(CalculatorError, match="example"):
        raise error_type("example")
