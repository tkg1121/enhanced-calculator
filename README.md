# Enhanced Calculator

My IS 601 calculator project. This version adds power and root operations,
CSV history, undo and redo, and environment settings.

## Setup

Use Python 3.11 or newer. GitHub Actions tests on Python 3.12.

```bash
git clone https://github.com/tkg1121/enhanced-calculator.git
cd enhanced-calculator
python -m venv .venv
```

Activate the environment in Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

On Linux or macOS, use `python3` when creating the environment, then activate it:

```bash
source .venv/bin/activate
```

Install dependencies and start the application from the project folder:

```bash
python -m pip install -r requirements.txt
python -m app
```

In VSCode, select the interpreter inside `.venv`.

## Using the calculator

Enter an operation name, then enter each number separately. Names are not
case-sensitive, and surrounding whitespace is ignored.

```text
Operation: power
First number: 2
Second number (exponent/degree for power/root): 3
Result: 8
Operation: root
First number: -27
Second number (exponent/degree for power/root): 3
Result: -3
Operation: undo
Undo complete.
Operation: history
operation  first  second  result
    power      2       3       8
Operation: exit

Goodbye.
```

| Operation | Meaning |
| --- | --- |
| `add` | first + second |
| `subtract` | first - second |
| `multiply` | first * second |
| `divide` | first / second; the divisor cannot be zero |
| `power` | first raised to second |
| `root` | second root of first; the degree cannot be zero |

Integers, decimals, negative numbers, and scientific notation are accepted.
`nan`, `inf`, `-inf`, and overflowing numbers are rejected with an error message.
This keeps nonfinite values out of both calculations and saved history.
Negative radicands require an odd integer degree. Negative degrees are allowed,
so `root 16 -2` means 1/4. A zero radicand with a negative degree is undefined.
Complex results are rejected. `power 0 0` returns 1, following Python's behavior.

Calculations use floating-point arithmetic. Small rounding differences and
underflow to zero are possible. Display precision does not change stored values.

## Commands

| Command | Behavior |
| --- | --- |
| `help` | Show operations and commands |
| `history` | Display the current DataFrame history |
| `clear` | Remove all current records; this can be undone |
| `undo` | Restore the history before the last successful change |
| `redo` | Reapply an undone change |
| `save` | Write the current history to the configured CSV |
| `load` | Validate and replace history from that CSV; this can be undone |
| `exit` | End the session |

Commands run at the operation prompt. `exit`, Ctrl+C, or end-of-input can end the
session at any prompt. Invalid inputs produce an error and return to the
operation prompt. Failed operations do not create history entries or undo states.

A new calculation, clear, or successful load discards the redo stack. Undo and
redo work within the current session; their stacks are not saved across restarts.

## Configuration

Copy `.env.example` to `.env` if you want to change the defaults. The app uses
`python-dotenv`; environment variables already set in the shell take precedence.

| Variable | Default | Accepted values |
| --- | --- | --- |
| `CALCULATOR_HISTORY_FILE` | `data/history.csv` | Nonempty file path |
| `CALCULATOR_LOG_FILE` | `data/calculator.log` | A different nonempty file path |
| `CALCULATOR_AUTOSAVE` | `true` | `true` or `false` |
| `CALCULATOR_PRECISION` | `10` | Integer from 1 to 17 significant digits |

Relative paths are resolved from the working directory. Missing parent
directories are created when saving or logging. Invalid settings stop startup
with a readable error and exit status 1.

## History and local logging

History is stored in a pandas DataFrame with the columns `operation`, `first`,
`second`, and `result`. Existing CSV history loads automatically at startup.
Every imported row is validated, including checking its saved result against
the arithmetic result with a small floating-point tolerance.

An invalid file is never partially loaded. Startup stops on invalid existing
history so the file cannot accidentally be overwritten by a fresh session.
Fix the file or select another history path to start again. A failed manual
load leaves the current history and undo/redo stacks intact.

With auto-save enabled, calculations, clear, undo, redo, and load write the
current history to CSV. Saving writes a temporary file in the same directory,
then replaces the destination only after writing succeeds. A failed write leaves
the previous CSV intact. Use one calculator session per history file; concurrent
sessions are not coordinated.

Observer failures produce warnings while retaining the in-memory history. If
auto-save fails, fix the file access or storage problem and use `save` before
exiting. If auto-save is disabled, changes require an explicit `save`; exiting
does not save them automatically. Existing history still loads on startup.

The logging observer appends local entries such as `calculate: 2 calculation(s)`.
No network logging is used. Runtime CSVs, logs, `.env`, and the virtual environment
are excluded from Git.

## Structure and design patterns

```text
app/
    __init__.py
    __main__.py
    calculator_repl.py
    calculation.py
    calculator_config.py
    calculator_memento.py
    exceptions.py
    history.py
    input_validators.py
    operations.py
tests/
    conftest.py
    test_calculations.py
    test_calculator_repl.py
    test_calculator_config.py
    test_calculator_memento.py
    test_exceptions.py
    test_history.py
    test_input_validators.py
    test_operations.py
```

| Pattern | Implementation |
| --- | --- |
| Strategy | Each arithmetic class implements the shared `Operation` interface |
| Factory | `OperationFactory.create()` chooses and instantiates the strategy |
| Observer | `Calculator` notifies logging and auto-save observers after changes; `subscribe()` accepts additional observers |
| Memento | Immutable `CalculatorMemento` snapshots and the `UndoRedo` caretaker preserve past and future history states |
| Facade | `Calculator` provides calculation, history, persistence, and undo/redo methods for the REPL |

Shared number validation and strategy execution avoid duplicated checks. LBYL
is used to reject unknown operations, zero divisors, and invalid root degrees
before performing arithmetic. EAFP is used when converting numbers and reading
or writing files: expected failures are caught and translated into application
errors. Error classes in `exceptions.py` let the REPL handle these consistently.

## Testing and CI

```bash
python -m pytest
```

`pyproject.toml` requires 100% line and branch coverage across all of `app`,
including the entry point. Tests use temporary directories, so running them does
not alter saved application history or logs. Parameterized tests cover each
required test module, including nonfinite numbers, domain errors, CSV validation,
observer failures, configuration, undo/redo, and prompt exits.

GitHub Actions installs dependencies and runs this same command on every push
and pull request. Failed tests or coverage below 100% fail the build.

Coverage exclusions such as `# pragma: no cover` remove code from the coverage
report and can also affect branch accounting. This project does not use them;
the error paths and entry point are tested. See the
[coverage.py exclusion documentation](https://coverage.readthedocs.io/en/7.14.1/excluding.html).
100% coverage measures executed code, not every possible combination of inputs.
