# Textual TUI

A terminal user interface for vibe-o-matic, built with [Textual](https://textual.textualize.io/).

This project is currently a minimal scaffold: it renders a header and footer, includes a single quit key binding, and provides the entry point for a future TUI experience. It does not yet integrate with oracle-cli or expose gameplay features.

## What you get today

- A working Textual app shell with header and footer widgets.
- A `vibe-tui` console script for launching the app.
- A small pytest suite that validates the core structure.

## Requirements

- Python 3.11 or newer.
- [uv](https://docs.astral.sh/uv/) for environment and dependency management (recommended).

## Install and run locally

From the `textual-tui` directory:

```bash
uv venv
source .venv/bin/activate
uv pip install -e .
vibe-tui
```

If you prefer to run the module directly:

```bash
python -m textual_tui.app
```

## Development workflow

Install the development dependencies:

```bash
uv pip install -e '.[dev]'
```

Run the app with live reloading:

```bash
textual run --dev textual_tui/app.py
```

## Testing

Run the test suite:

```bash
uv pip install -e '.[dev]'
pytest tests -v
```

## Key bindings

- `q`: Quit the application.

## Project layout

```
textual-tui/
├── textual_tui/   # Application package
├── tests/         # Pytest suite
├── pyproject.toml # Package metadata and dependencies
└── README.md      # This document
```

## Contributing

See [CLAUDE.md](CLAUDE.md) for architecture notes, code style expectations, and contribution guidance.
