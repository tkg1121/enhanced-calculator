"""Immutable record of a completed calculation."""

from dataclasses import dataclass

from app.input_validators import validate_number
from app.operations import OperationFactory


@dataclass(frozen=True)
class Calculation:
    """Store the operation, operands, and result together."""

    operation: str
    first: float
    second: float
    result: float

    @classmethod
    def create(cls, operation: str, first, second):
        """Use the factory and selected strategy to create a valid record."""
        strategy = OperationFactory.create(operation)
        first, second = validate_number(first), validate_number(second)
        return cls(operation.strip().lower(), first, second, strategy.execute(first, second))
