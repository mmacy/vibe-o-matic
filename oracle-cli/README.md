# Oracle CLI

A stateless Oracle CLI tool implementing the core oracles from Old-School Solo for solo tabletop RPG play.

## Features

- **Closed Oracle**: Ask yes/no questions with likelihood modifiers
- **Muse**: Get thematic inspiration words from 10 different themes
- **Plot Twist**: Generate random plot twists with subject + action
- **Chaos Dice**: Track chaos pool with stateless dice rolling

## Installation

Using `uv` (recommended):

```bash
uv tool install .
```

Using `pip`:

```bash
pip install .
```

## Usage

### Closed Oracle

Ask yes/no questions with likelihood modifiers:

```bash
oracle closed --question "Is the door locked?" --likelihood likely
oracle closed -q "Is it raining?" -l very_unlikely
```

Likelihood options: `very_unlikely`, `unlikely`, `even` (default), `likely`, `very_likely`

### Muse

Get inspiration words from theme tables:

```bash
oracle muse --theme Change --count 3
oracle muse -t Social -t Swords -c 6
```

Available themes: `Change`, `Social`, `Swords`, `Sorcery`, `Divine`, `Monstrous`, `Treasure`, `Wilderness`, `Talk`, `Place`

### Plot Twist

Generate a random plot twist:

```bash
oracle twist
```

### Chaos Dice

Roll chaos dice and track the pool:

```bash
oracle chaos-roll --dice 4
oracle chaos-roll -d 6
```

## Global Options

All commands support:

- `--format [text|json]`: Output format (default: text)
- `--seed INTEGER`: Seed for deterministic output (useful for testing or LLM integration)

Examples:

```bash
oracle closed -q "Is it safe?" --format json --seed 42
oracle muse -t Change -c 2 --format json --seed 123
```

## Running as a Module

You can also run the CLI as a Python module:

```bash
python -m oracle closed -q "Is the door locked?"
```

## Development

### Running Tests

```bash
uv run pytest
```

### Project Structure

```
oracle/
  core/        # Pure functional logic
  tables/      # YAML data files
  util/        # Shared utilities
  cli.py       # Typer CLI interface
tests/         # Test suite
```

See [docs/DESIGN.md](docs/DESIGN.md) for detailed technical specifications.

## License

See LICENSE file for details.
