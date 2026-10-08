"""Errors that can be shown directly to the calculator user."""


class CalculatorError(Exception):
    """Base error for expected application failures."""


class ValidationError(CalculatorError):
    """An operand is not a finite real number."""


class OperationError(CalculatorError):
    """An operation is unknown or undefined for its operands."""


class ConfigurationError(CalculatorError):
    """An application setting is invalid."""


class HistoryError(CalculatorError):
    """History could not be read or written safely."""


class StateError(CalculatorError):
    """There is no state available to undo or redo."""
