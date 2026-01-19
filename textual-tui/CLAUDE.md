# CLAUDE.md - Guide for AI Assistants

This document helps Claude (and other AI assistants) understand the textual-tui project structure, conventions, and best practices for contributing to this codebase.

## Project Overview

**textual-tui** is a terminal user interface (TUI) application for the vibe-o-matic suite of solo tabletop RPG tools. It's built using the [Textual](https://textual.textualize.io/) framework, which provides a modern, reactive approach to building terminal UIs with Python.

### Current Status

This is a newly scaffolded project with minimal functionality:
- Basic app structure with Header and Footer widgets
- Single key binding ('q' to quit)
- Comprehensive test suite with 5 passing tests
- Ready for feature development

## Architecture

### Project Structure

```
textual-tui/
├── textual_tui/           # Main package
│   ├── __init__.py        # Package initialization
│   └── app.py             # Main VibeTUI application class
├── tests/                 # Test suite
│   ├── __init__.py
│   └── test_app.py        # Tests for VibeTUI
├── .venv/                 # Virtual environment (git-ignored)
├── pyproject.toml         # Project metadata and dependencies
└── README.md              # User-facing documentation
```

### Key Components

- **VibeTUI (app.py)**: Main application class inheriting from `textual.app.App`
- **compose() method**: Defines the widget tree structure
- **BINDINGS**: List of key binding tuples `(key, action, description)`

## Development Guidelines

### Code Style

This project follows the **Google Python Style Guide**:

- Use Google-style docstrings for all modules, classes, and functions
- Include comprehensive docstrings that help new developers understand the code
- Provide usage examples in docstrings for public APIs
- Document all function parameters, return values, and exceptions
- Import order: standard library, third-party, local (alphabetized within groups)

### Testing

- All tests use pytest with pytest-asyncio for async support
- Use Textual's `run_test()` context manager for testing app functionality
- Aim for meaningful tests that verify actual behavior, not just imports
- Each test should have a comprehensive docstring explaining what it validates

**Running tests:**

```bash
# From the textual-tui directory
source .venv/bin/activate
pytest tests -v
```

### Dependency Management

This repo uses **uv** for Python dependency management:

```bash
# Create virtual environment
uv venv

# Install in development mode
uv pip install -e '.[dev]'

# Install the package as a tool
uv tool install .
```

### Dependencies

**Runtime:**
- `textual>=0.85.0` - TUI framework
- `anthropic>=0.40.0` - Claude Agents SDK

**Development:**
- `textual-dev>=1.0.0` - Development tools for Textual
- `pytest>=8.0.0` - Testing framework
- `pytest-asyncio>=0.23.0` - Async test support

## Common Tasks

### Adding a New Widget

1. Import the widget from `textual.widgets`
2. Yield it in the `compose()` method
3. Add tests to verify it's properly mounted
4. Update docstrings to document the new widget

Example:

```python
from textual.widgets import Header, Footer, Static

class VibeTUI(App):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Hello, world!")  # New widget
        yield Footer()
```

### Adding a New Key Binding

1. Add tuple to `BINDINGS` class attribute: `(key, action, description)`
2. Implement the action method: `def action_<name>(self) -> None:`
3. Add test to verify the binding works

Example:

```python
BINDINGS = [
    ("q", "quit", "Quit"),
    ("h", "show_help", "Help"),  # New binding
]

def action_show_help(self) -> None:
    """Show help dialog."""
    # Implementation here
```

### Adding a New Screen

Textual uses Screens for different views. To add a new screen:

1. Create a Screen subclass
2. Implement its `compose()` method
3. Use `self.push_screen()` or `self.switch_screen()` to navigate
4. Add tests for the new screen

## Testing Patterns

### Basic App Test

```python
@pytest.mark.asyncio
async def test_something():
    """Test description."""
    app = VibeTUI()
    async with app.run_test() as pilot:
        # Test the app using pilot
        await pilot.press("q")
        assert not app.is_running
```

### Widget Query Test

```python
async with app.run_test() as pilot:
    widget = app.query_one(WidgetType)
    assert widget is not None
```

### User Interaction Test

```python
async with app.run_test() as pilot:
    await pilot.press("enter")
    await pilot.pause()
    # Verify results
```

## Integration with Vibe-o-matic

This TUI is part of the larger vibe-o-matic monorepo:

- **oracle-cli**: Python CLI tool for solo RPG oracles (sibling directory)
- **ai-gm**: React SPA for AI-powered game mastering (sibling directory)

You may want to integrate with oracle-cli's core logic located in `oracle-cli/oracle/core/` for dice rolling, oracle tables, etc.

## Textual Best Practices

1. **Composition over inheritance**: Build UIs by composing widgets, not deep inheritance
2. **Reactive attributes**: Use `reactive` for state that should trigger re-renders
3. **Message passing**: Use Textual's message system for component communication
4. **CSS styling**: Prefer CSS for styling over hardcoded styles
5. **Test with run_test()**: Always test using Textual's test harness

## Resources

- [Textual Documentation](https://textual.textualize.io/)
- [Textual Tutorial](https://textual.textualize.io/tutorial/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [pytest Documentation](https://docs.pytest.org/)

## Current Limitations

- No CSS styling defined yet
- No custom widgets implemented
- No screens beyond the default
- No integration with oracle-cli or AI features yet
- No configuration system

## Next Steps for Development

When extending this application, consider:

1. **Define the app's purpose**: What specific features from oracle-cli or ai-gm should this TUI provide?
2. **Design the UI**: Sketch out screens, widgets, and navigation flow
3. **Add custom widgets**: Build reusable components for common UI patterns
4. **Implement features**: Add oracle queries, dice rolling, character management, etc.
5. **Add CSS styling**: Create a cohesive visual design
6. **Error handling**: Add user-friendly error messages and recovery
7. **Configuration**: Allow users to customize the experience

## Questions to Ask the User

When working on this project, consider asking:

- What specific features should the TUI provide?
- Should it integrate with oracle-cli's existing functionality?
- What's the target user experience (quick CLI tool vs. immersive interface)?
- Are there specific oracle tables or game systems to support?
- Should it connect to Claude API for AI features?

---

*This document should be updated as the project evolves. Future Claude instances: please update this file when you add significant new features or architectural changes.*
