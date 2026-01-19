# Textual TUI

A terminal user interface for vibe-o-matic, built with [Textual](https://textual.textualize.io/).

This TUI provides an interactive command-line experience for solo tabletop RPG tools with rich formatting and keyboard navigation.

## Installation

```bash
# Install as a tool with uv
uv tool install .

# Or install in development mode
uv pip install -e .

# Or with development dependencies
uv pip install -e '.[dev]'
```

## Usage

Run the TUI:

```bash
vibe-tui
```

Or run directly with Python:

```bash
python -m textual_tui.app
```

## Development

For development with live editing and debugging:

```bash
uv pip install -e '.[dev]'
textual run --dev textual_tui/app.py
```

## Testing

Run the test suite:

```bash
uv pip install -e '.[dev]'
pytest tests -v
```

## Key Bindings

- `q` - Quit the application

## Contributing

See [CLAUDE.md](CLAUDE.md) for detailed information about the project architecture, development guidelines, and how to contribute.
