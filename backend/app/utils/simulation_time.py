"""Gemeinsame Abbildung von Simulationsrunden auf lokale Uhrzeit und Tag."""

from typing import List, Sequence, Tuple


def simulation_clock(
    round_num: int, minutes_per_round: int, start_hour: int = 7
) -> Tuple[int, int]:
    """Liefert (Tag ab 1, Stunde 0–23) für den Beginn einer Runde."""
    absolute_minutes = start_hour * 60 + round_num * minutes_per_round
    return absolute_minutes // (24 * 60) + 1, (absolute_minutes // 60) % 24


def hours_covered_by_round(
    round_num: int, minutes_per_round: int, start_hour: int = 7
) -> List[int]:
    """Stunden (0–23), die eine Runde von ihrem Start an überstreicht.

    Bei minutes_per_round > 60 reicht ein reiner Startstunden-Check nicht:
    eine 4-h-Runde ab 07:00 deckt 7–10 ab und muss Aktivitätsfenster dort treffen.
    """
    if minutes_per_round <= 0:
        raise ValueError("minutes_per_round muss positiv sein")
    _, start = simulation_clock(round_num, minutes_per_round, start_hour)
    return [
        ((start * 60 + offset) // 60) % 24
        for offset in range(0, minutes_per_round, 60)
    ]


def peak_multiplier_for_hours(
    hours: Sequence[int],
    peak_hours: Sequence[int],
    off_peak_hours: Sequence[int],
    peak_multiplier: float = 1.5,
    off_peak_multiplier: float = 0.3,
) -> float:
    """Stärkster Multiplikator unter den überstrichenen Stunden (Peak gewinnt)."""
    peak = set(peak_hours)
    off = set(off_peak_hours)
    values = []
    for hour in hours:
        if hour in peak:
            values.append(peak_multiplier)
        elif hour in off:
            values.append(off_peak_multiplier)
        else:
            values.append(1.0)
    return max(values) if values else 1.0
