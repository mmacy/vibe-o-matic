# Oracle CLI — Design & Technical Specification

## 1. Overview

This document defines the design of a stateless Oracle CLI tool implementing the core oracles from Old-School Solo:

* Closed Oracle (yes/no/and/but/because + scenario + tone)
* Muse (theme table lookup)
* Plot Twist (subject + action generator)
* Chaos Dice (stateless pool tracking)

The tool is designed for:

* Direct human CLI use
* Agent/LLM invocation (via deterministic JSON output)

Technical Constraints:

* Pure and stateless.
* Deterministic when seeded (--seed).
* Installable via uv tool install .
* Stack: Python 3.13, typer, rich, pyyaml, hatchling.

## 2. Architecture

### 2.1 Package Structure

```
oracle/
  __init__.py
  __main__.py       # Entry point for python -m oracle
  cli.py            # Typer app definition
  core/             # Pure functional logic
    closed.py
    muse.py
    twist.py
    chaos.py
  tables/           # Static YAML data
    closed.yaml
    muse.yaml
    twist.yaml
  util/             # Shared helpers
    rng.py
    formats.py
tests/              # Deterministic pytest suite
  conftest.py
  test_closed.py
  test_muse.py
  test_twist.py
  test_chaos.py
pyproject.toml
DESIGN.md
```

### 2.2 Boundaries

* core/: Pure functions only. Input: Parameters + RNG. Output: Dataclasses. No print statements.
* cli.py: Handles I/O, argument parsing (Typer), and formatting (Rich/JSON).
* tables/: Static data loaded via importlib.resources.

## 3. CLI Specification

Global Arguments:

* --format [text|json]: Defaults to text.
* --seed INTEGER: Optional. Seeds the internal RNG for deterministic output.

### 3.1 Command: closed

Usage:
```
oracle closed --question "Is the door locked?" --likelihood likely
```

Likelihood Enum (StrEnum):

* very_unlikely (-2)
* unlikely (-1)
* even (0) [Default]
* likely (+1)
* very_likely (+2)

Logic:

* Roll 1d6 + modifier.
* Clamp result to [1, 6].
* Lookup result in tables/closed.yaml.

JSON Output:
```json
{
  "type": "closed",
  "question": "Is the door locked?",
  "likelihood": "likely",
  "roll": { "base": 4, "modifier": 1, "final": 5 },
  "result": {
    "answer": "yes",
    "detail": "but",
    "scenario": "expected",
    "tone": "unfortunately"
  }
}
```

Text Output (Rich):
```
[bold green]YES[/] (but...)
[dim]Roll: 4 + 1 = 5[/]
```

### 3.2 Command: muse

Usage:
```
oracle muse --theme Change --theme Social --count 1
```

Logic:

* Load tables/muse.yaml.
* For N count:
  * Select theme (round-robin if multiple provided).
  * Roll 1d20.
  * Lookup word.

JSON Output:
```json
{
  "type": "muse",
  "results": [
    { "theme": "Change", "roll": 20, "word": "Reverse" },
    { "theme": "Social", "roll": 5, "word": "Friend" }
  ]
}
```

### 3.3 Command: twist

Usage:
```
oracle twist
```

Logic:

* Roll 1d6 for Subject (lookup in tables/twist.yaml).
* Roll 1d6 for Action (lookup in tables/twist.yaml).

JSON Output:
```json
{
  "type": "twist",
  "rolls": { "subject": 6, "action": 2 },
  "result": "An item alters the location."
}
```

### 3.4 Command: chaos-roll

Usage:
```
oracle chaos-roll --dice 4
```

Logic:

* Roll N d6s.
* Count sixes.
* Calculate remaining dice (total - sixes).
* Determine if event triggers (remaining == 0).

JSON Output:
```json
{
  "type": "chaos",
  "input_pool": 4,
  "rolls": [2, 6, 3, 6],
  "sixes": 2,
  "next_pool": 2,
  "triggered": false
}
```

## 4. Implementation Details

### 4.1 RNG Wrapper (util/rng.py)

Encapsulate random.Random.

```python
class OracleRNG:
    def __init__(self, seed: int | None = None):
        self._rng = random.Random(seed)

    def d6(self) -> int: ...
    def d20(self) -> int: ...
```

### 4.2 Table Loading

Use importlib.resources to ensure compatibility with uv tool install (zip-safe).

```python
from importlib.resources import files
import yaml

def load_table(filename: str) -> dict:
    content = files("oracle.tables").joinpath(filename).read_text(encoding="utf-8")
    return yaml.safe_load(content)
```

## 5. Packaging (pyproject.toml)

Uses Hatchling (default for uv) for build backend.

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "oracle-cli"
version = "0.1.0"
description = "Old-School Solo Oracle CLI"
requires-python = ">=3.13"
dependencies = [
    "typer>=0.12.0",
    "rich>=13.0.0",
    "pyyaml>=6.0.0",
]

[project.scripts]
oracle = "oracle.cli:app"

# CRITICAL: Include YAML files in the build
[tool.hatch.build.targets.wheel]
packages = ["oracle"]

[tool.hatch.build.targets.sdist]
include = ["oracle/tables/*.yaml"]
```

## 6. Testing Strategy

Run via uv run pytest.

* Determinism: Verify that passing --seed 123 returns identical JSON output across runs for all commands.
* Table Integrity: Test that every row in closed.yaml (1-6) is reachable.
* Chaos Logic: Verify next_pool calculation logic (e.g., input 1, roll 6 -> next 0 -> trigger True).
* CLI Parsing: Verify StrEnum validation for --likelihood (rejects invalid strings).
