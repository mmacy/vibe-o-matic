"""CLI interface for Oracle using Typer."""

import json
from dataclasses import asdict
from enum import Enum
from typing import Annotated, Optional

import typer
from rich.console import Console

from oracle.core import (
    Likelihood,
    ask_closed,
    ask_muse,
    ask_twist,
    chaos_roll,
    roll_dice,
)
from oracle.util import OracleRNG

app = typer.Typer(
    name="oracle",
    help="Old-School Solo Oracle CLI - Tools for solo RPG players to answer questions, generate inspiration, and introduce chaos into their game sessions.",
    add_completion=False,
)
console = Console()


class OutputFormat(str, Enum):
    """Output format options."""

    TEXT = "text"
    JSON = "json"


@app.callback()
def callback():
    """Old-School Solo Oracle CLI."""
    pass


@app.command()
def closed(
    question: Annotated[
        str, typer.Option(..., "--question", "-q", help="The yes/no question to ask")
    ],
    likelihood: Annotated[
        Likelihood,
        typer.Option(
            "--likelihood",
            "-l",
            help="Likelihood of positive answer. Valid values: very_unlikely, unlikely, even, likely, very_likely",
        ),
    ] = Likelihood.EVEN,
    seed: Annotated[
        Optional[int],
        typer.Option("--seed", "-s", help="Random seed for deterministic output"),
    ] = None,
    output_format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = OutputFormat.TEXT,
):
    """Ask a closed (yes/no) question.

    Roll a d6 with modifiers to get a YES/NO answer along with context like scenario and tone.

    Examples:
      oracle closed -q "Is the door locked?" -l likely
      oracle closed -q "Does the guard notice me?" -l very_unlikely
    """
    rng = OracleRNG(seed)
    result = ask_closed(question, likelihood, rng)

    if output_format == OutputFormat.JSON:
        print(json.dumps(asdict(result), indent=2))
    else:
        # Text output with Rich formatting
        answer = result.result.answer.upper()
        detail = f" ({result.result.detail})" if result.result.detail else ""

        # Color based on answer
        if answer == "YES":
            console.print(f"[bold green]{answer}[/]{detail}")
        else:
            console.print(f"[bold red]{answer}[/]{detail}")

        console.print(
            f"[dim]Roll: {result.roll.base} + {result.roll.modifier} = {result.roll.final}[/]"
        )
        console.print(f"[dim]Scenario: {result.result.scenario}[/]")
        console.print(f"[dim]Tone: {result.result.tone}[/]")


@app.command()
def muse(
    theme: Annotated[
        list[str],
        typer.Option(
            ...,
            "--theme",
            "-t",
            help="Theme(s) to use (round-robin if multiple). Valid themes: Change, Divine, Monstrous, Place, Social, Sorcery, Swords, Talk, Treasure, Wilderness",
        ),
    ],
    count: Annotated[
        int, typer.Option("--count", "-c", help="Number of words to generate")
    ] = 1,
    seed: Annotated[
        Optional[int],
        typer.Option("--seed", "-s", help="Random seed for deterministic output"),
    ] = None,
    output_format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = OutputFormat.TEXT,
):
    """Get inspiration words from theme tables.

    Roll on thematic d20 tables to generate evocative words for creative inspiration.
    When multiple themes are specified, words are drawn round-robin from each theme.

    Examples:
      oracle muse -t Change
      oracle muse -t Swords -t Sorcery -c 5
      oracle muse -t Wilderness -t Treasure -c 10
    """
    if not theme:
        typer.echo("Error: At least one --theme is required", err=True)
        raise typer.Exit(1)

    rng = OracleRNG(seed)

    try:
        result = ask_muse(theme, count, rng)
    except KeyError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    if output_format == OutputFormat.JSON:
        print(json.dumps(asdict(result), indent=2))
    else:
        # Text output with Rich formatting
        for r in result.results:
            console.print(f"[bold cyan]{r.theme}[/] (d20={r.roll}): [bold]{r.word}[/]")


@app.command()
def twist(
    seed: Annotated[
        Optional[int],
        typer.Option("--seed", "-s", help="Random seed for deterministic output"),
    ] = None,
    output_format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = OutputFormat.TEXT,
):
    """Generate a plot twist.

    Roll for a random subject and action combination to create unexpected story developments.
    Useful for adding surprise elements or complications to your solo game.

    Examples:
      oracle twist
      oracle twist -s 42
    """
    rng = OracleRNG(seed)
    result = ask_twist(rng)

    if output_format == OutputFormat.JSON:
        print(json.dumps(asdict(result), indent=2))
    else:
        # Text output with Rich formatting
        console.print(f"[bold magenta]{result.result}[/]")
        console.print(
            f"[dim]Subject: {result.rolls.subject}, Action: {result.rolls.action}[/]"
        )


@app.command(name="chaos-roll")
def chaos_roll_cmd(
    dice: Annotated[
        int,
        typer.Option(
            ..., "--dice", "-d", help="Number of d6s to roll (current pool size)"
        ),
    ],
    seed: Annotated[
        Optional[int],
        typer.Option("--seed", "-s", help="Random seed for deterministic output"),
    ] = None,
    output_format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = OutputFormat.TEXT,
):
    """Roll chaos dice and track the pool.

    Roll Nd6 and count the sixes. The next pool size = current pool - sixes rolled.
    If the pool reaches 0, an event is triggered! Use this to add unpredictable
    tension and escalation to your solo game sessions.

    Examples:
      oracle chaos-roll -d 6
      oracle chaos-roll -d 3 -s 123
    """
    if dice < 1:
        typer.echo("Error: dice must be >= 1", err=True)
        raise typer.Exit(1)

    rng = OracleRNG(seed)
    result = chaos_roll(dice, rng)

    if output_format == OutputFormat.JSON:
        print(json.dumps(asdict(result), indent=2))
    else:
        # Text output with Rich formatting
        console.print(f"[bold]Rolls:[/] {result.rolls}")
        console.print(f"[bold yellow]Sixes:[/] {result.sixes}")
        console.print(f"[bold]Next Pool:[/] {result.next_pool}")

        if result.triggered:
            console.print("[bold red]⚠ EVENT TRIGGERED! ⚠[/]")
        else:
            console.print("[dim]No event triggered[/]")


@app.command()
def roll(
    notation: Annotated[
        str, typer.Argument(help="Dice notation (e.g., 1d20, 2d6+3, 1d8-1)")
    ],
    seed: Annotated[
        Optional[int],
        typer.Option("--seed", "-s", help="Random seed for deterministic rolling"),
    ] = None,
    output_format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = OutputFormat.TEXT,
):
    """Roll polyhedral dice using standard notation.

    Supports standard polyhedral dice (d4, d6, d8, d10, d12, d20, d100) and any
    arbitrary-sided die. Accepts modifiers in the notation (e.g., +3, -1).

    Examples:
      oracle roll 1d20              # Roll a d20
      oracle roll 2d6+3             # Roll 2d6 and add 3
      oracle roll 1d8-1             # Roll 1d8 and subtract 1
      oracle roll 3d6               # Roll 3d6 (e.g., ability score)
      oracle roll 1d100 --seed 42   # Deterministic percentile roll
    """
    try:
        rng = OracleRNG(seed)
        result = roll_dice(notation, rng)

        if output_format == OutputFormat.JSON:
            print(json.dumps(asdict(result), indent=2))
        else:
            # Text output with Rich formatting
            console.print(f"\n[bold]{result.notation}[/bold]")

            # Show individual rolls
            roll_display = ", ".join([f"[cyan]{r.roll}[/cyan]" for r in result.rolls])
            console.print(f"Rolls ({result.count}d{result.sides}): {roll_display}")

            # Show modifier if present
            if result.modifier != 0:
                sign = "+" if result.modifier > 0 else ""
                console.print(f"Modifier: {sign}{result.modifier}")

            # Show total
            console.print(f"\n[bold green]Total: {result.total}[/bold green]\n")

    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
