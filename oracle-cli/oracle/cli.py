"""CLI interface for Oracle using Typer."""

import json
from dataclasses import asdict
from enum import Enum
from typing import Annotated, Optional

import typer
from rich.console import Console

from oracle.core import Likelihood, ask_closed, ask_muse, ask_twist, chaos_roll
from oracle.util import OracleRNG

app = typer.Typer(
    name="oracle",
    help="Old-School Solo Oracle CLI",
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
    question: Annotated[str, typer.Option(..., "--question", "-q", help="The yes/no question to ask")],
    likelihood: Annotated[
        Likelihood,
        typer.Option("--likelihood", "-l", help="Likelihood of positive answer"),
    ] = Likelihood.EVEN,
    seed: Annotated[
        Optional[int],
        typer.Option("--seed", "-s", help="Random seed for deterministic output"),
    ] = None,
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = OutputFormat.TEXT,
):
    """Ask a closed (yes/no) question."""
    rng = OracleRNG(seed)
    result = ask_closed(question, likelihood, rng)

    if format == OutputFormat.JSON:
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
        console.print(f"[dim]{result.result.scenario}[/]")
        console.print(f"[dim]{result.result.tone}[/]")


@app.command()
def muse(
    theme: Annotated[
        list[str],
        typer.Option(..., "--theme", "-t", help="Theme(s) to use (round-robin if multiple)"),
    ],
    count: Annotated[int, typer.Option("--count", "-c", help="Number of words to generate")] = 1,
    seed: Annotated[
        Optional[int],
        typer.Option("--seed", "-s", help="Random seed for deterministic output"),
    ] = None,
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = OutputFormat.TEXT,
):
    """Get inspiration words from theme tables."""
    if not theme:
        console.print("[red]Error: At least one --theme is required[/]")
        raise typer.Exit(1)

    rng = OracleRNG(seed)

    try:
        result = ask_muse(theme, count, rng)
    except KeyError as e:
        console.print(f"[red]Error: {e}[/]")
        raise typer.Exit(1)

    if format == OutputFormat.JSON:
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
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = OutputFormat.TEXT,
):
    """Generate a plot twist."""
    rng = OracleRNG(seed)
    result = ask_twist(rng)

    if format == OutputFormat.JSON:
        print(json.dumps(asdict(result), indent=2))
    else:
        # Text output with Rich formatting
        console.print(f"[bold magenta]{result.result}[/]")
        console.print(
            f"[dim]Subject: {result.rolls.subject}, Action: {result.rolls.action}[/]"
        )


@app.command(name="chaos-roll")
def chaos_roll_cmd(
    dice: Annotated[int, typer.Option(..., "--dice", "-d", help="Number of d6s to roll")],
    seed: Annotated[
        Optional[int],
        typer.Option("--seed", "-s", help="Random seed for deterministic output"),
    ] = None,
    format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format"),
    ] = OutputFormat.TEXT,
):
    """Roll chaos dice and track the pool."""
    rng = OracleRNG(seed)
    result = chaos_roll(dice, rng)

    if format == OutputFormat.JSON:
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


if __name__ == "__main__":
    app()
