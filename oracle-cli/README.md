# Oracle CLI

A stateless Oracle CLI tool implementing the core oracles from Old-School Solo for solo tabletop RPG play.

## Features

- **Closed Oracle**: Ask yes/no questions with likelihood modifiers
- **Muse**: Get thematic inspiration words from 10 different themes
- **Plot Twist**: Generate random plot twists with subject + action
- **Chaos Dice**: Track chaos pool with stateless dice rolling
- **Dice Roller**: Roll polyhedral dice with standard notation (d4, d6, d8, d10, d12, d20, d100)

## Documentation

- **[Command reference](docs/COMMAND_REFERENCE.md)**: Complete reference for all commands with detailed examples
- **[Design documentation](docs/DESIGN.md)**: Technical specifications and architecture

## Installation

Using `uv` (recommended):

```bash
uv tool install .
```

Using `pip`:

```bash
pip install .
```

## Quick start

View available commands and options:

```bash
oracle --help
oracle closed --help
oracle muse --help
```

## Usage

The Oracle CLI provides five core commands for solo RPG play. See the [command reference](docs/COMMAND_REFERENCE.md) for complete documentation.

### Closed Oracle - answer yes/no questions

Ask yes/no questions with likelihood modifiers:

```bash
# Basic question (50/50 odds)
oracle closed -q "Is the door locked?"

# With likelihood modifier
oracle closed -q "Does the guard notice me?" -l very_unlikely

# More likely outcomes
oracle closed -q "Is there a tavern nearby?" -l likely
```

**Likelihood options:** `very_unlikely`, `unlikely`, `even` (default), `likely`, `very_likely`

Output includes the answer (YES/NO), roll details, scenario context, and tone.

### Muse - get thematic inspiration

Get inspiration words from thematic d20 tables:

```bash
# Single inspiration word
oracle muse -t Change

# Multiple words from one theme
oracle muse -t Swords -c 5

# Alternate between themes (round-robin)
oracle muse -t Wilderness -t Treasure -c 6
```

**Available themes:** `Change`, `Divine`, `Monstrous`, `Place`, `Social`, `Sorcery`, `Swords`, `Talk`, `Treasure`, `Wilderness`

Each theme provides 20 evocative words for creative inspiration.

### Twist - generate plot twists

Generate random plot twists for unexpected story developments:

```bash
oracle twist
```

Combines a random subject with a random action to create surprising complications.

### Chaos roll - track chaos pool

Roll chaos dice to add unpredictable events:

```bash
# Roll chaos pool (typically start with 6)
oracle chaos-roll -d 6

# Roll smaller pool after sixes removed
oracle chaos-roll -d 3
```

**How it works:** Roll Nd6, count the sixes. Next pool = current pool - sixes. When pool reaches 0, an event triggers!

### Roll - roll polyhedral dice

Roll any polyhedral dice using standard notation:

```bash
# Attack roll
oracle roll 1d20

# Damage with modifier
oracle roll 1d8+2

# Multiple dice
oracle roll 2d6

# Ability score
oracle roll 3d6

# Percentile
oracle roll 1d100
```

**Dice notation:** `[count]d[sides][+/-modifier]`

Supports all standard polyhedrals (d4, d6, d8, d10, d12, d20, d100) and any arbitrary-sided die.

## Advanced usage

### Global options

All commands support:

- `--format, -f [text|json]`: Output format (default: `text`)
- `--seed, -s INTEGER`: Random seed for deterministic output

Examples:

```bash
# Get JSON output for parsing
oracle closed -q "Is it safe?" -f json

# Use a seed for reproducible results
oracle muse -t Change -c 2 -s 42
```

### Example solo play session

Here's a quick example of using multiple oracles together:

```bash
# Does the party find the hidden temple?
$ oracle closed -q "Do we find the hidden temple?" -l likely
YES (and...)
Roll: 5 + 1 = 6

# What's the temple like?
$ oracle muse -t Place -t Divine -c 3
Place (d20=17): Crypt
Divine (d20=8): Spirit
Place (d20=13): Cave

# A random complication appears!
$ oracle twist
An ancient curse awakens
```

### Running as a module

You can also run the CLI as a Python module:

```bash
python -m oracle closed -q "Is the door locked?"
```

## Development

### Running Tests

```bash
uv run pytest
```

### Project structure

```
oracle/
  core/        # Pure functional logic
  tables/      # YAML data files
  util/        # Shared utilities
  cli.py       # Typer CLI interface
tests/         # Test suite
```

## License

See LICENSE file for details.
