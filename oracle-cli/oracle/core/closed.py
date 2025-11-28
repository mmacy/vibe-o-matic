"""Closed Oracle: Yes/No questions with modifiers."""

from dataclasses import dataclass
from enum import StrEnum

from oracle.util import OracleRNG, load_table


class Likelihood(StrEnum):
    """Likelihood modifier for closed questions."""

    VERY_UNLIKELY = "very_unlikely"
    UNLIKELY = "unlikely"
    EVEN = "even"
    LIKELY = "likely"
    VERY_LIKELY = "very_likely"

    def modifier(self) -> int:
        """Get the numeric modifier for this likelihood.

        Returns:
            Integer modifier from -2 to +2.
        """
        modifiers = {
            Likelihood.VERY_UNLIKELY: -2,
            Likelihood.UNLIKELY: -1,
            Likelihood.EVEN: 0,
            Likelihood.LIKELY: 1,
            Likelihood.VERY_LIKELY: 2,
        }
        return modifiers[self]


@dataclass
class ClosedRoll:
    """Roll details for a closed question."""

    base: int
    modifier: int
    final: int


@dataclass
class ClosedResult:
    """Result details for a closed question."""

    answer: str
    detail: str | None
    scenario: str
    tone: str


@dataclass
class ClosedQuery:
    """Complete result of a closed oracle query."""

    type: str
    question: str
    likelihood: str
    roll: ClosedRoll
    result: ClosedResult


def ask_closed(
    question: str,
    likelihood: Likelihood,
    rng: OracleRNG,
) -> ClosedQuery:
    """Ask a closed (yes/no) question.

    Args:
        question: The question to ask.
        likelihood: The likelihood of a positive answer.
        rng: Random number generator.

    Returns:
        Complete query result with roll and outcome.
    """
    # Load the closed oracle table
    table = load_table("closed.yaml")

    # Roll 1d6
    base_roll = rng.d6()

    # Apply modifier
    modifier = likelihood.modifier()
    modified_roll = base_roll + modifier

    # Clamp to [1, 6]
    final_roll = max(1, min(6, modified_roll))

    # Lookup result in table
    result_data = table["rows"][final_roll]

    # Build result
    roll = ClosedRoll(base=base_roll, modifier=modifier, final=final_roll)
    result = ClosedResult(
        answer=result_data["answer"],
        detail=result_data["detail"],
        scenario=result_data["scenario"],
        tone=result_data["tone"],
    )

    return ClosedQuery(
        type="closed",
        question=question,
        likelihood=likelihood.value,
        roll=roll,
        result=result,
    )
