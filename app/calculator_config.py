"""Validated environment settings, with optional .env defaults."""

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv

from app.exceptions import ConfigurationError


@dataclass(frozen=True)
class CalculatorConfig:
    """Paths, persistence preference, and display precision."""

    history_file: Path = Path("data/history.csv")
    log_file: Path = Path("data/calculator.log")
    autosave: bool = True
    precision: int = 10

    def __post_init__(self):
        if not isinstance(self.autosave, bool):
            raise ConfigurationError("CALCULATOR_AUTOSAVE must be true or false.")
        if type(self.precision) is not int or not 1 <= self.precision <= 17:
            raise ConfigurationError("CALCULATOR_PRECISION must be an integer from 1 to 17.")
        if self.history_file.resolve() == self.log_file.resolve():
            raise ConfigurationError("History and log files must have different paths.")
        for path in (self.history_file, self.log_file):
            if path.is_dir():
                raise ConfigurationError(f"Expected a file path, not a directory: {path}")

    @classmethod
    def from_env(cls, env_file=".env"):
        """Read .env without overriding existing environment variables."""
        try:
            load_dotenv(env_file, override=False)
            autosave = os.getenv("CALCULATOR_AUTOSAVE", "true").strip().lower()
            if autosave not in {"true", "false"}:
                raise ConfigurationError("CALCULATOR_AUTOSAVE must be true or false.")
            paths = []
            for key, default in (("HISTORY_FILE", "data/history.csv"), ("LOG_FILE", "data/calculator.log")):
                value = os.getenv(f"CALCULATOR_{key}", default).strip()
                if not value:
                    raise ConfigurationError(f"CALCULATOR_{key} cannot be empty.")
                paths.append(Path(value).expanduser())
            precision = int(os.getenv("CALCULATOR_PRECISION", "10"))
            return cls(*paths, autosave == "true", precision)
        except (ValueError, OSError) as error:
            raise ConfigurationError(f"Cannot read configuration: {error}") from error
