# Oracle package

This package provides the stateless oracle logic that powers the Oracle CLI, exposing pure functions for closed questions, muse inspiration, plot twists, and chaos dice. The modules are designed for deterministic execution when paired with a seeded random number generator.

## Key components

- `oracle.core.closed.ask_closed`: Resolves a yes/no question with likelihood modifiers and returns detailed roll metadata.
- `oracle.core.muse.ask_muse`: Rotates through one or more themed tables to return inspiration words.
- `oracle.core.twist.ask_twist`: Rolls a plot twist by combining subject and action entries.
- `oracle.core.chaos.roll_chaos`: Rolls chaos dice and reports how the pool escalates or resets.
- `oracle.util.OracleRNG`: Wraps `random.Random` to deliver deterministic dice rolls across the oracles.

## Installing

Install the package locally while in the repository root:

```bash
pip install .
```

To develop against the project without installing globally, use editable mode:

```bash
pip install -e .
```

## Using the oracles programmatically

Import the pure functions and provide a seeded `OracleRNG` when you need repeatable outcomes:

```python
from oracle.core.closed import Likelihood, ask_closed
from oracle.core.muse import ask_muse
from oracle.util import OracleRNG

rng = OracleRNG(seed=123)

closed_query = ask_closed(
    question="Is the door locked?",
    likelihood=Likelihood.LIKELY,
    rng=rng,
)
print(closed_query.result.answer)

muse_query = ask_muse(themes=["Change", "Social"], count=3, rng=rng)
print([result.word for result in muse_query.results])
```

## Data tables

Oracle outcomes are stored in YAML files under `oracle/tables`. The helpers in `oracle.util.formats` load the tables at runtime so they can be extended without code changes.
