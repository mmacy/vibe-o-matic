"""Plot Twist Oracle: Subject + Action generator."""

from dataclasses import dataclass

from oracle.util import OracleRNG, load_table


@dataclass
class TwistRolls:
    """Roll details for a plot twist."""

    subject: int
    action: int


@dataclass
class TwistQuery:
    """Complete result of a plot twist query."""

    type: str
    rolls: TwistRolls
    result: str


def ask_twist(rng: OracleRNG) -> TwistQuery:
    """Generate a plot twist.

    Args:
        rng: Random number generator.

    Returns:
        Complete query result with subject, action, and combined text.
    """
    # Load the twist table
    table = load_table("twist.yaml")

    # Roll for subject and action
    subject_roll = rng.d6()
    action_roll = rng.d6()

    # Lookup in table
    subject = table["subject"][subject_roll]
    action = table["action"][action_roll]

    # Combine into result text
    result = f"{subject} {action}"

    rolls = TwistRolls(subject=subject_roll, action=action_roll)

    return TwistQuery(type="twist", rolls=rolls, result=result)
