"""Tests for the Muse Oracle."""

import pytest

from oracle.core import ask_muse
from oracle.util import OracleRNG


def test_muse_determinism():
    """Test that the same seed produces the same result."""
    rng1 = OracleRNG(seed=123)
    result1 = ask_muse(["Change"], 3, rng1)

    rng2 = OracleRNG(seed=123)
    result2 = ask_muse(["Change"], 3, rng2)

    assert result1 == result2


def test_muse_single_theme(seeded_rng):
    """Test muse with a single theme."""
    result = ask_muse(["Change"], 3, seeded_rng)

    assert result.type == "muse"
    assert len(result.results) == 3
    for r in result.results:
        assert r.theme == "Change"
        assert 1 <= r.roll <= 20
        assert isinstance(r.word, str)


def test_muse_round_robin():
    """Test that multiple themes rotate properly."""
    rng = OracleRNG(seed=42)
    result = ask_muse(["Change", "Social", "Swords"], 6, rng)

    assert len(result.results) == 6
    # Should cycle: Change, Social, Swords, Change, Social, Swords
    assert result.results[0].theme == "Change"
    assert result.results[1].theme == "Social"
    assert result.results[2].theme == "Swords"
    assert result.results[3].theme == "Change"
    assert result.results[4].theme == "Social"
    assert result.results[5].theme == "Swords"


def test_muse_invalid_theme():
    """Test that invalid theme raises KeyError."""
    rng = OracleRNG(seed=42)

    with pytest.raises(KeyError) as exc_info:
        ask_muse(["InvalidTheme"], 1, rng)

    assert "InvalidTheme" in str(exc_info.value)


def test_muse_all_themes():
    """Test that all expected themes are available."""
    rng = OracleRNG(seed=42)
    expected_themes = [
        "Change",
        "Social",
        "Swords",
        "Sorcery",
        "Divine",
        "Monstrous",
        "Treasure",
        "Wilderness",
        "Talk",
        "Place",
    ]

    for theme in expected_themes:
        result = ask_muse([theme], 1, rng)
        assert result.results[0].theme == theme
