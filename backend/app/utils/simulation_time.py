"""Gemeinsame Abbildung von Simulationsrunden auf lokale Uhrzeit und Tag."""

from typing import Tuple


def simulation_clock(
    round_num: int, minutes_per_round: int, start_hour: int = 7
) -> Tuple[int, int]:
    """Liefert (Tag ab 1, Stunde 0–23) für den Beginn einer Runde."""
    absolute_minutes = start_hour * 60 + round_num * minutes_per_round
    return absolute_minutes // (24 * 60) + 1, (absolute_minutes // 60) % 24
