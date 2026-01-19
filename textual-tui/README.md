# Textual TUI

A terminal user interface for vibe-o-matic, built with [Textual](https://textual.textualize.io/).

## Installation

```bash
# Install in development mode
pip install -e .

# Or with development dependencies
pip install -e '.[dev]'
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
pip install -e '.[dev]'
textual run --dev textual_tui/app.py
```

## Key Bindings

- `q` - Quit the application
