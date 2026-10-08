"""Interchangeable arithmetic strategies and their factory."""

from abc import ABC, abstractmethod
import math

from app.exceptions import OperationError
from app.input_validators import validate_number


class Operation(ABC):
    """Validate operands and results around an arithmetic strategy."""

    def execute(self, first, second) -> float:
        first, second = validate_number(first), validate_number(second)
        try:
            result = self._calculate(first, second)
        except (ValueError, OverflowError) as error:
            raise OperationError("Result is undefined or too large for real numbers.") from error
        if not math.isfinite(result):
            raise OperationError("Result is too large for a finite number.")
        return result

    @abstractmethod
    def _calculate(self, first: float, second: float) -> float:
        """Execute this strategy on validated operands."""


class Add(Operation):
    """Addition strategy."""

    def _calculate(self, first, second):
        return first + second


class Subtract(Operation):
    """Subtraction strategy."""

    def _calculate(self, first, second):
        return first - second


class Multiply(Operation):
    """Multiplication strategy."""

    def _calculate(self, first, second):
        return first * second


class Divide(Operation):
    """Division strategy with an explicit domain check."""

    def _calculate(self, first, second):
        # LBYL: reject the zero divisor before performing division.
        if second == 0:
            raise OperationError("Cannot divide by zero.")
        return first / second


class Power(Operation):
    """Raise the first operand to the second operand."""

    def _calculate(self, first, second):
        return math.pow(first, second)


class Root(Operation):
    """Take the second operand's root of the first operand."""

    def _calculate(self, first, second):
        if second == 0:
            raise OperationError("Root degree cannot be zero.")
        if first < 0:
            if not second.is_integer() or second % 2 == 0:
                raise OperationError("Negative numbers require an odd integer root degree.")
            return -math.pow(-first, 1 / second)
        return math.pow(first, 1 / second)


class OperationFactory:
    """Build a strategy from the operation name entered by the user."""

    strategies = {
        "add": Add, "subtract": Subtract, "multiply": Multiply,
        "divide": Divide, "power": Power, "root": Root,
    }

    @classmethod
    def create(cls, name: str) -> Operation:
        name = name.strip().lower()
        if name not in cls.strategies:
            raise OperationError("Choose add, subtract, multiply, divide, power, or root.")
        return cls.strategies[name]()
