"""Muse Oracle: Theme-based word inspiration."""

from dataclasses import dataclass

from oracle.util import OracleRNG, load_table


@dataclass
class MuseResult:
    """Single muse word result."""

    theme: str
    roll: int
    word: str


@dataclass
class MuseQuery:
    """Complete result of a muse oracle query."""

    type: str
    results: list[MuseResult]


def ask_muse(
    themes: list[str],
    count: int,
    rng: OracleRNG,
) -> MuseQuery:
    """Get inspiration words from theme tables.

    Args:
        themes: List of theme names to use (round-robin).
        count: Number of words to generate.
        rng: Random number generator.

    Returns:
        Complete query result with all words.

    Raises:
        KeyError: If a theme name is not found in the table.
    """
    # Load the muse table
    table = load_table("muse.yaml")
    theme_tables = table["themes"]

    # Validate all themes exist
    for theme in themes:
        if theme not in theme_tables:
            available = ", ".join(sorted(theme_tables.keys()))
            raise KeyError(
                f"Theme '{theme}' not found. Available themes: {available}"
            )

    results: list[MuseResult] = []

    # Generate words (round-robin through themes if multiple)
    for i in range(count):
        theme = themes[i % len(themes)]
        roll = rng.d20()
        word = theme_tables[theme][roll]

        results.append(MuseResult(theme=theme, roll=roll, word=word))

    return MuseQuery(type="muse", results=results)
