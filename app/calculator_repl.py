"""Calculator facade, event coordination, and terminal interface."""

from app.calculation import Calculation
from app.calculator_config import CalculatorConfig
from app.calculator_memento import UndoRedo
from app.exceptions import CalculatorError
from app.history import AutoSaveObserver, History, LoggingObserver
from app.operations import OperationFactory


HELP = """Operations: add, subtract, multiply, divide, power, root.
Enter the operation, then the two numbers when prompted.
Power means first ** second; root means the second root of the first.
Commands: help, history, clear, undo, redo, save, load, exit.
Use commands at the operation prompt; exit works at any prompt.
Only finite real numbers are accepted."""


class Calculator:
    """Facade for arithmetic, history, undo/redo, and event observers."""

    def __init__(self, config: CalculatorConfig):
        self.config = config
        self.history = History()
        self.states = UndoRedo()
        self.observers = [LoggingObserver(config.log_file)]
        self.warnings = []
        if config.autosave:
            self.observers.append(AutoSaveObserver(config.history_file))
        if config.history_file.exists():
            self.history.load(config.history_file)

    def subscribe(self, observer):
        """Register another object with an update(event, history) method."""
        if observer not in self.observers:
            self.observers.append(observer)

    def _notify(self, event):
        self.warnings.clear()
        for observer in self.observers:
            try:
                observer.update(event, self.history)
            except (CalculatorError, OSError) as error:
                self.warnings.append(f"{type(observer).__name__}: {error}")

    def calculate(self, operation, first, second) -> Calculation:
        calculation = Calculation.create(operation, first, second)
        self.states.record(self.history.frame)
        self.history.append(calculation)
        self._notify("calculate")
        return calculation

    def clear(self):
        self.states.record(self.history.frame)
        self.history.clear()
        self._notify("clear")

    def undo(self):
        self.history.frame = self.states.undo(self.history.frame)
        self._notify("undo")

    def redo(self):
        self.history.frame = self.states.redo(self.history.frame)
        self._notify("redo")

    def save(self):
        """Save explicitly even when auto-save is disabled."""
        self.history.save(self.config.history_file)

    def load(self):
        """Load as an undoable replacement, only after validation succeeds."""
        loaded = History()
        loaded.load(self.config.history_file)
        self.states.record(self.history.frame)
        self.history.frame = loaded.frame
        self._notify("load")

    def show_history(self) -> str:
        if self.history.frame.empty:
            return "History is empty."
        return self.history.frame.to_string(index=False, float_format=lambda value: f"{value:.{self.config.precision}g}")


def read_input(prompt: str) -> str:
    """Share whitespace and exit handling across all prompts."""
    text = input(prompt).strip().lower()
    if text == "exit":
        raise EOFError
    return text


def run(calculator: Calculator):
    """Keep accepting operations until exit, EOF, or Ctrl+C."""
    print(HELP)
    actions = {name: getattr(calculator, name) for name in ("clear", "undo", "redo", "save", "load")}
    while True:
        try:
            command = read_input("Operation: ")
            if command == "help":
                print(HELP)
            elif command == "history":
                print(calculator.show_history())
            elif command in actions:
                actions[command]()
                print(f"{command.capitalize()} complete.")
            else:
                OperationFactory.create(command)
                first = read_input("First number: ")
                second = read_input("Second number (exponent/degree for power/root): ")
                calculation = calculator.calculate(command, first, second)
                print(f"Result: {calculation.result:.{calculator.config.precision}g}")
            for warning in calculator.warnings:
                print(f"Warning: {warning}. History remains in memory.")
            calculator.warnings.clear()
        except CalculatorError as error:
            print(f"Error: {error}")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            return


def main() -> int:
    """Report configuration/startup failures without an unhandled traceback."""
    try:
        calculator = Calculator(CalculatorConfig.from_env())
    except CalculatorError as error:
        print(f"Startup error: {error}")
        return 1
    run(calculator)
    return 0
