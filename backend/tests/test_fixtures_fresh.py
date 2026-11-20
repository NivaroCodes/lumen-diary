"""Фикстуры совпадают с результатом боевого конвейера на сырых данных."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import regenerate_fixtures as regen  # noqa: E402
from app.text_analysis import analyze_text  # noqa: E402
from conftest import FIXTURE_NAMES, load_fixture  # noqa: E402


def test_fixtures_are_fresh():
    built = regen.build_all()
    assert set(built) == set(FIXTURE_NAMES)
    for name, data in built.items():
        assert load_fixture(name) == data, f"{name}: запустите scripts/regenerate_fixtures.py"
        assert (regen.FIXTURES_DIR / f"{name}.json").read_text(encoding="utf-8") == regen.render(data)


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_raw_text_matches_profile_text(name):
    fx = load_fixture(name)
    assert analyze_text(fx["text"]) == fx["profile"]["text"]


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_seed_is_uint32(name):
    assert 0 <= load_fixture(name)["visual"]["seed"] <= 2**32 - 1
