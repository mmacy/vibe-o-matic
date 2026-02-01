"""Test fixtures for the Vibe Orchestrator.

Provides fake executables for testing agent drivers:
- codex: Fake Codex CLI executable
- claude: Fake Claude CLI executable
"""

from pathlib import Path

FIXTURES_DIR = Path(__file__).parent
FAKE_CODEX_PATH = FIXTURES_DIR / "codex"
FAKE_CLAUDE_PATH = FIXTURES_DIR / "claude"
