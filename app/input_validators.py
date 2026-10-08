"""Shared validation for interactive input and imported history."""

import math

from app.exceptions import ValidationError


def validate_number(value) -> float:
    """Accept numeric input only when it represents a finite real number."""
    # EAFP: attempt conversion and translate conversion failures.
    try:
        number = float(value)
    except (ValueError, TypeError, OverflowError) as error:
        raise ValidationError("Enter a number, such as 4 or -2.5.") from error
    if not math.isfinite(number):
        raise ValidationError("NaN and infinity are not accepted; use finite numbers.")
    return number
