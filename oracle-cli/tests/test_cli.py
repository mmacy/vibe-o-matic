"""Integration tests for the CLI commands."""

import json

from typer.testing import CliRunner

from oracle.cli import app

runner = CliRunner()


def test_closed_command_text_output():
    """Test closed command with text output."""
    result = runner.invoke(
        app, ["closed", "-q", "Is the door locked?", "-l", "likely", "--seed", "42"]
    )
    assert result.exit_code == 0
    assert "YES" in result.stdout or "NO" in result.stdout
    assert "Roll:" in result.stdout


def test_closed_command_json_output():
    """Test closed command with JSON output."""
    result = runner.invoke(
        app,
        [
            "closed",
            "-q",
            "Is the door locked?",
            "-l",
            "likely",
            "--seed",
            "42",
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0

    # Parse JSON output
    output = json.loads(result.stdout)
    assert output["type"] == "closed"
    assert output["question"] == "Is the door locked?"
    assert output["likelihood"] == "likely"
    assert "roll" in output
    assert "result" in output


def test_closed_command_determinism():
    """Test that same seed produces same output."""
    result1 = runner.invoke(
        app,
        ["closed", "-q", "Test?", "--seed", "123", "--format", "json"],
    )
    result2 = runner.invoke(
        app,
        ["closed", "-q", "Test?", "--seed", "123", "--format", "json"],
    )

    assert result1.exit_code == 0
    assert result2.exit_code == 0
    assert result1.stdout == result2.stdout


def test_closed_command_requires_question():
    """Test that closed command requires question parameter."""
    result = runner.invoke(app, ["closed"])
    assert result.exit_code != 0


def test_muse_command_text_output():
    """Test muse command with text output."""
    result = runner.invoke(app, ["muse", "-t", "Change", "-c", "3", "--seed", "42"])
    assert result.exit_code == 0
    assert "Change" in result.stdout


def test_muse_command_json_output():
    """Test muse command with JSON output."""
    result = runner.invoke(
        app,
        ["muse", "-t", "Change", "-c", "2", "--seed", "42", "--format", "json"],
    )
    assert result.exit_code == 0

    output = json.loads(result.stdout)
    assert output["type"] == "muse"
    assert len(output["results"]) == 2
    assert all(r["theme"] == "Change" for r in output["results"])


def test_muse_command_multiple_themes():
    """Test muse command with multiple themes (round-robin)."""
    result = runner.invoke(
        app,
        [
            "muse",
            "-t",
            "Change",
            "-t",
            "Social",
            "-c",
            "4",
            "--seed",
            "42",
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0

    output = json.loads(result.stdout)
    assert len(output["results"]) == 4
    # Should alternate: Change, Social, Change, Social
    assert output["results"][0]["theme"] == "Change"
    assert output["results"][1]["theme"] == "Social"
    assert output["results"][2]["theme"] == "Change"
    assert output["results"][3]["theme"] == "Social"


def test_muse_command_requires_theme():
    """Test that muse command requires theme parameter."""
    result = runner.invoke(app, ["muse"])
    assert result.exit_code != 0


def test_muse_command_invalid_theme():
    """Test muse command with invalid theme."""
    result = runner.invoke(app, ["muse", "-t", "InvalidTheme", "-c", "1"])
    assert result.exit_code != 0
    assert "InvalidTheme" in result.stderr


def test_twist_command_text_output():
    """Test twist command with text output."""
    result = runner.invoke(app, ["twist", "--seed", "42"])
    assert result.exit_code == 0
    assert "Subject:" in result.stdout
    assert "Action:" in result.stdout


def test_twist_command_json_output():
    """Test twist command with JSON output."""
    result = runner.invoke(app, ["twist", "--seed", "42", "--format", "json"])
    assert result.exit_code == 0

    output = json.loads(result.stdout)
    assert output["type"] == "twist"
    assert "rolls" in output
    assert "result" in output
    assert 1 <= output["rolls"]["subject"] <= 6
    assert 1 <= output["rolls"]["action"] <= 6


def test_chaos_roll_command_text_output():
    """Test chaos-roll command with text output."""
    result = runner.invoke(app, ["chaos-roll", "-d", "4", "--seed", "42"])
    assert result.exit_code == 0
    assert "Rolls:" in result.stdout
    assert "Sixes:" in result.stdout
    assert "Next Pool:" in result.stdout


def test_chaos_roll_command_json_output():
    """Test chaos-roll command with JSON output."""
    result = runner.invoke(
        app, ["chaos-roll", "-d", "5", "--seed", "42", "--format", "json"]
    )
    assert result.exit_code == 0

    output = json.loads(result.stdout)
    assert output["type"] == "chaos"
    assert output["input_pool"] == 5
    assert len(output["rolls"]) == 5
    assert output["next_pool"] == output["input_pool"] - output["sixes"]
    assert isinstance(output["triggered"], bool)


def test_chaos_roll_command_requires_dice():
    """Test that chaos-roll command requires dice parameter."""
    result = runner.invoke(app, ["chaos-roll"])
    assert result.exit_code != 0


def test_all_commands_support_seed():
    """Test that all commands support --seed for determinism."""
    # Closed
    r1 = runner.invoke(
        app, ["closed", "-q", "Test?", "--seed", "999", "--format", "json"]
    )
    r2 = runner.invoke(
        app, ["closed", "-q", "Test?", "--seed", "999", "--format", "json"]
    )
    assert r1.stdout == r2.stdout

    # Muse
    r1 = runner.invoke(
        app, ["muse", "-t", "Change", "-c", "1", "--seed", "999", "--format", "json"]
    )
    r2 = runner.invoke(
        app, ["muse", "-t", "Change", "-c", "1", "--seed", "999", "--format", "json"]
    )
    assert r1.stdout == r2.stdout

    # Twist
    r1 = runner.invoke(app, ["twist", "--seed", "999", "--format", "json"])
    r2 = runner.invoke(app, ["twist", "--seed", "999", "--format", "json"])
    assert r1.stdout == r2.stdout

    # Chaos
    r1 = runner.invoke(
        app, ["chaos-roll", "-d", "3", "--seed", "999", "--format", "json"]
    )
    r2 = runner.invoke(
        app, ["chaos-roll", "-d", "3", "--seed", "999", "--format", "json"]
    )
    assert r1.stdout == r2.stdout


def test_roll_command_text_output():
    """Test roll command with text output."""
    result = runner.invoke(app, ["roll", "1d20", "--seed", "42"])
    assert result.exit_code == 0
    assert "1d20" in result.stdout
    assert "Total:" in result.stdout


def test_roll_command_json_output():
    """Test roll command with JSON output."""
    result = runner.invoke(app, ["roll", "2d6+3", "--seed", "42", "--format", "json"])
    assert result.exit_code == 0

    output = json.loads(result.stdout)
    assert output["type"] == "roll"
    assert output["notation"] == "2d6+3"
    assert output["count"] == 2
    assert output["sides"] == 6
    assert output["modifier"] == 3
    assert len(output["rolls"]) == 2
    assert "total" in output


def test_roll_command_determinism():
    """Test that same seed produces same output."""
    result1 = runner.invoke(app, ["roll", "2d6+3", "--seed", "123", "--format", "json"])
    result2 = runner.invoke(app, ["roll", "2d6+3", "--seed", "123", "--format", "json"])

    assert result1.exit_code == 0
    assert result2.exit_code == 0
    assert result1.stdout == result2.stdout


def test_roll_command_all_polyhedrals():
    """Test all common polyhedral dice."""
    for sides in [4, 6, 8, 10, 12, 20, 100]:
        result = runner.invoke(
            app, ["roll", f"1d{sides}", "--seed", "42", "--format", "json"]
        )
        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert output["sides"] == sides


def test_roll_command_with_negative_modifier():
    """Test roll with negative modifier."""
    result = runner.invoke(app, ["roll", "1d8-1", "--seed", "42", "--format", "json"])
    assert result.exit_code == 0

    output = json.loads(result.stdout)
    assert output["modifier"] == -1


def test_roll_command_invalid_notation():
    """Test roll command with invalid notation."""
    result = runner.invoke(app, ["roll", "invalid"])
    assert result.exit_code != 0
    assert "Error:" in result.stderr or "Error:" in result.stdout


def test_roll_command_requires_notation():
    """Test that roll command requires notation argument."""
    result = runner.invoke(app, ["roll"])
    assert result.exit_code != 0
