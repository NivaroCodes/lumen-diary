"""Три фикстуры заметно различаются (если тест падает, менять тексты, а не пороги)."""
from __future__ import annotations

from conftest import FIXTURE_NAMES, load_fixture


def visuals() -> list[dict]:
    return [load_fixture(n)["visual"] for n in FIXTURE_NAMES]


def test_density_spread():
    values = [v["density"]["value"] for v in visuals()]
    assert max(values) - min(values) >= 0.5


def test_light_direction_all_different():
    assert len({v["light"]["direction_deg"] for v in visuals()}) == 3


def test_line_trajectory_all_different():
    assert len({v["line"]["trajectory"] for v in visuals()}) == 3


def test_palettes_all_different():
    palettes = [tuple(v["palette"]["colors"]) for v in visuals()]
    assert len(set(palettes)) == 3


def test_text_profile_targets():
    t = {n: load_fixture(n)["profile"]["text"] for n in FIXTURE_NAMES}
    calm, energy, dense = t["day-calm"], t["day-energy"], t["day-dense"]
    assert (calm["time_of_day"], calm["weather"]) == ("evening", "rain")
    assert (energy["time_of_day"], energy["weather"]) == ("morning", "sun")
    assert (dense["time_of_day"], dense["weather"]) == ("day", "fog")
    assert 1 <= calm["events_count"] <= 2 and 40 <= calm["length_words"] <= 70
    assert 4 <= energy["events_count"] <= 6 and 100 <= energy["length_words"] <= 160
    assert 7 <= dense["events_count"] <= 10 and 180 <= dense["length_words"] <= 260
