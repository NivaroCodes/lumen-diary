"""Правила R-* из docs/mapping.md и фикстуры day-*.json."""
from __future__ import annotations

import copy

import pytest

from app.visual_model import build_visual, compute_seed
from conftest import FIXTURE_NAMES, load_fixture



def assert_close(actual, expected, path=""):
    if isinstance(expected, dict):
        assert set(actual) == set(expected), path
        for k in expected:
            assert_close(actual[k], expected[k], f"{path}.{k}")
    else:
        assert actual == expected, path


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_fixture_visual_matches_rules(name):
    fx = load_fixture(name)
    visual, _ = build_visual(fx["profile"], fx["visual"]["seed"], fx["visual"]["caption"])
    assert_close(visual, fx["visual"])


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_fixture_explain_matches(name):
    fx = load_fixture(name)
    _, explain = build_visual(fx["profile"], fx["visual"]["seed"], fx["visual"]["caption"])
    expected = {e["param"]: e for e in fx["explain"]}
    assert {e["param"] for e in explain} == set(expected)
    for entry in explain:
        exp = expected[entry["param"]]
        assert entry["rule"] == exp["rule"]
        assert entry["source"] == exp["source"]
        assert entry["provenance"] == exp["provenance"]
        assert_close(entry["value"], exp["value"], entry["param"])
        assert entry["text_ru"]


def test_every_visual_param_has_explain():
    fx = load_fixture("day-calm")
    visual, explain = build_visual(fx["profile"], 1, "x")
    params = {e["param"] for e in explain}
    expected = {
        "light.direction_deg", "light.intensity", "light.temperature_k", "palette.colors",
        "palette.saturation", "density.value", "density.elements", "texture.weather",
        "texture.grain", "texture.blur", "line.trajectory", "line.amplitude",
        "line.roughness", "line.color_index", "motion.reveal_ms", "motion.pulse_ms",
        "motion.character", "motion.scene", "contrast",
    }
    assert params == expected
    assert {e["rule"] for e in explain} == {
        "R-LIGHT-01", "R-LIGHT-02", "R-LIGHT-03", "R-PAL-01", "R-PAL-02", "R-DEN-01", "R-DEN-02",
        "R-TEX-01", "R-TEX-02", "R-TEX-03", "R-LINE-01", "R-LINE-02", "R-LINE-03", "R-LINE-04",
        "R-MOT-01", "R-MOT-02", "R-MOT-03", "R-MOT-04", "R-CON-01",
    }


def test_deterministic():
    fx = load_fixture("day-energy")
    a = build_visual(fx["profile"], 7, "c")
    b = build_visual(copy.deepcopy(fx["profile"]), 7, "c")
    assert a == b


def test_seed_deterministic_and_input_sensitive():
    base = compute_seed("текст", ["h1", "h2"], "https://a.b", "описание")
    assert base == compute_seed("текст", ["h1", "h2"], "https://a.b", "описание")
    assert base != compute_seed("текст!", ["h1", "h2"], "https://a.b", "описание")
    assert base != compute_seed("текст", ["h2", "h1"], "https://a.b", "описание")
    assert base != compute_seed("текст", ["h1", "h2"], "https://a.c", "описание")
    assert base != compute_seed("текст", ["h1", "h2"], "https://a.b", "иное")
    assert 0 <= base <= 2**32 - 1


def _profile_variant(**changes):
    fx = load_fixture("day-calm")
    profile = copy.deepcopy(fx["profile"])
    for path, value in changes.items():
        section, key = path.split("__")
        profile[section][key] = value
    return profile


def _flat(d, prefix=""):
    out = {}
    for k, v in d.items():
        if isinstance(v, dict):
            out.update(_flat(v, f"{prefix}{k}."))
        else:
            out[f"{prefix}{k}"] = v
    return out


def _changed(a, b):
    fa, fb = _flat(a), _flat(b)
    return {k for k in fa if fa[k] != fb[k]}


def test_tempo_changes_only_motion_and_blur():
    base, _ = build_visual(_profile_variant(), 1, "c")
    other, _ = build_visual(_profile_variant(music__tempo_bpm=140), 1, "c")
    assert _changed(base, other) == {"texture.blur", "motion.reveal_ms", "motion.pulse_ms"}


def test_photos_change_only_photo_params():
    base, _ = build_visual(_profile_variant(), 1, "c")
    other, _ = build_visual(
        _profile_variant(photos__brightness=0.9, photos__contrast=0.9, photos__warmth=0.1,
                         photos__dominant_colors=["#111111", "#222222", "#333333"]), 1, "c")
    assert _changed(base, other) <= {
        "palette.colors", "palette.saturation", "light.intensity", "light.temperature_k",
        "texture.grain", "contrast",  # R-CON-01 зависит от контраста фото
    }
    assert {"palette.colors", "light.intensity", "light.temperature_k", "texture.grain"} <= _changed(base, other)


def test_text_changes_only_text_params():
    base, _ = build_visual(_profile_variant(), 1, "c")
    other, _ = build_visual(
        _profile_variant(text__time_of_day="morning", text__weather="fog", text__events_count=9,
                         text__length_words=250), 1, "c")
    assert _changed(base, other) <= {
        "light.direction_deg", "density.value", "density.elements", "texture.weather", "line.trajectory",
        "motion.scene",  # R-MOT-04: погода из текста задаёт сцену
    }
    assert len(_changed(base, other)) == 6


@pytest.mark.parametrize("tod,direction,traj", [
    ("morning", 90, "rising"), ("day", 180, "wave"), ("evening", 270, "falling"),
    ("night", 0, "flat"), ("unknown", 90, "wave"),
])
def test_r_light_01_and_r_line_01(tod, direction, traj):
    visual, explain = build_visual(_profile_variant(text__time_of_day=tod), 1, "c")
    assert visual["light"]["direction_deg"] == direction
    assert visual["line"]["trajectory"] == traj
    entry = next(e for e in explain if e["rule"] == "R-LIGHT-01")
    assert entry["provenance"] == ("unknown" if tod == "unknown" else "measured")


def test_r_light_02_03():
    v, _ = build_visual(_profile_variant(photos__brightness=1.0, photos__warmth=1.0), 1, "c")
    assert v["light"]["intensity"] == pytest.approx(0.9)
    assert v["light"]["temperature_k"] == 2700
    v, _ = build_visual(_profile_variant(photos__brightness=0.0, photos__warmth=0.0), 1, "c")
    assert v["light"]["intensity"] == pytest.approx(0.2)
    assert v["light"]["temperature_k"] == 6500


def test_r_pal_01_one_photo_takes_three_colors():
    colors = ["#111111", "#222222", "#333333", "#444444", "#555555"]
    one, _ = build_visual(_profile_variant(photos__count=1, photos__dominant_colors=colors), 1, "c")
    many, _ = build_visual(_profile_variant(photos__count=2, photos__dominant_colors=colors), 1, "c")
    assert one["palette"]["colors"] == colors[:3]
    assert many["palette"]["colors"] == colors


def test_palette_padded_to_three_colors():
    v, _ = build_visual(_profile_variant(photos__count=1, photos__dominant_colors=["#010101"]), 1, "c")
    assert len(v["palette"]["colors"]) == 3
    assert v["palette"]["colors"][0] == "#010101"


def test_r_pal_02_saturation():
    v, _ = build_visual(_profile_variant(photos__contrast=1.0), 1, "c")
    assert v["palette"]["saturation"] == pytest.approx(0.7)


def test_r_den_01_02_caps():
    v, _ = build_visual(_profile_variant(text__events_count=12, text__length_words=900), 1, "c")
    assert v["density"] == {"value": 1.0, "elements": 12}
    v, _ = build_visual(_profile_variant(text__events_count=0, text__length_words=0), 1, "c")
    assert v["density"] == {"value": 0.0, "elements": 2}


@pytest.mark.parametrize("weather,expected", [("rain", "rain"), ("fog", "fog"), ("sun", "none"),
                                              ("snow", "none"), ("none", "none"), ("unknown", "none")])
def test_r_tex_01(weather, expected):
    v, _ = build_visual(_profile_variant(text__weather=weather), 1, "c")
    assert v["texture"]["weather"] == expected


def test_r_tex_02_grain():
    v, _ = build_visual(_profile_variant(photos__brightness=0.0), 1, "c")
    assert v["texture"]["grain"] == pytest.approx(0.5)
    v, _ = build_visual(_profile_variant(photos__brightness=1.0), 1, "c")
    assert v["texture"]["grain"] == 0.0


@pytest.mark.parametrize("tempo,blur,reveal,pulse", [
    (60, 0.6, 3100, 1000), (79, 0.6, 2815, 759), (80, 0.3, 2800, 750), (110, 0.3, 2350, 545 + 55),
    (111, 0.1, 2335, 600), (200, 0.1, 1000, 600), (220, 0.1, 800, 600), (40, 0.6, 3400, 1500),
    (None, 0.1, 2400, 1400),
])
def test_r_tex_03_and_r_mot(tempo, blur, reveal, pulse):
    v, _ = build_visual(_profile_variant(music__tempo_bpm=tempo), 1, "c")
    assert v["texture"]["blur"] == blur
    assert v["motion"]["reveal_ms"] == reveal
    assert v["motion"]["pulse_ms"] == pulse


def test_r_line_02_03_energy_and_genre():
    v, _ = build_visual(_profile_variant(music__energy=1.0, music__genre="rock"), 1, "c")
    assert v["line"]["amplitude"] == pytest.approx(0.9)
    assert v["line"]["roughness"] == pytest.approx(0.8)
    v, _ = build_visual(_profile_variant(music__energy=None, music__genre="unknown"), 1, "c")
    assert v["line"]["amplitude"] == 0.3
    assert v["line"]["roughness"] == 0.2
    v, _ = build_visual(_profile_variant(music__energy=0.0, music__genre="electronic"), 1, "c")
    assert v["line"]["roughness"] == pytest.approx(0.3)
    v, _ = build_visual(_profile_variant(music__energy=None), 1, "c")
    assert v["line"]["color_index"] == 0


def test_unknown_music_inputs_marked_unknown_in_explain():
    _, explain = build_visual(_profile_variant(music__tempo_bpm=None, music__energy=None), 1, "c")
    by_rule = {e["rule"]: e for e in explain}
    assert by_rule["R-MOT-01"]["provenance"] == "unknown"
    assert by_rule["R-LINE-02"]["provenance"] == "unknown"


@pytest.mark.parametrize("mode,delta", [("minor", 0.1), ("major", -0.05), ("unknown", 0.0)])
def test_r_con_01(mode, delta):
    v, _ = build_visual(_profile_variant(photos__contrast=0.5, music__mode=mode), 1, "c")
    assert v["contrast"] == pytest.approx(0.5 + delta)


def test_r_con_01_clamped():
    v, _ = build_visual(_profile_variant(photos__contrast=0.0, music__mode="major"), 1, "c")
    assert 0.0 <= v["contrast"] <= 1.0
    v, _ = build_visual(_profile_variant(photos__contrast=1.0, music__mode="minor"), 1, "c")
    assert v["contrast"] == 0.8


@pytest.mark.parametrize("mode,character,prov", [
    ("major", "smooth", "entered"), ("minor", "sharp", "entered"), ("unknown", "neutral", "unknown"),
])
def test_r_mot_03_character_from_mode(mode, character, prov):
    visual, explain = build_visual(_profile_variant(music__mode=mode), 1, "c")
    assert visual["motion"]["character"] == character
    item = next(e for e in explain if e["param"] == "motion.character")
    assert item["rule"] == "R-MOT-03" and item["provenance"] == prov
    if mode == "unknown":
        assert "неизвестен" in item["text_ru"]


def test_mode_changes_only_character_and_contrast():
    base, _ = build_visual(_profile_variant(music__mode="minor"), 1, "c")
    other, _ = build_visual(_profile_variant(music__mode="major"), 1, "c")
    assert _changed(base, other) == {"motion.character", "contrast"}


@pytest.mark.parametrize("weather,scene,texture", [
    ("rain", "rain", "rain"), ("fog", "fog", "fog"), ("sun", "sun", "none"),
    ("cloud", "cloud", "none"), ("snow", "snow", "none"), ("none", "still", "none"),
])
def test_r_mot_04_scene_from_text_weather(weather, scene, texture):
    visual, explain = build_visual(_profile_variant(text__weather=weather), 1, "c")
    assert visual["motion"]["scene"] == scene
    assert visual["texture"]["weather"] == texture
    assert next(e for e in explain if e["param"] == "motion.scene")["rule"] == "R-MOT-04"


def test_chosen_weather_overrides_text_weather():
    profile = _profile_variant(text__weather="sun")
    profile["context"] = {"weather": "rain", "weather_source": "chosen", "place": None}
    visual, explain = build_visual(profile, 1, "c")
    assert visual["motion"]["scene"] == "rain" and visual["texture"]["weather"] == "rain"
    tex = next(e for e in explain if e["param"] == "texture.weather")
    assert tex["source"] == "context.weather" and tex["provenance"] == "entered"
    assert "отмечен в записи" in tex["text_ru"]
