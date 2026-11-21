"""TEAM-04: парные проверки «один вход меняется — меняются только его параметры».

Матрица взята из docs/mapping.md (R-правила), а не из кода. Для каждого из трёх дней фикстур
и каждого из трёх входов (время суток, яркость фото, темп песни) берём пару: исходный вход и
изменённый, отличающийся только одним полем. Проверяем точное множество изменившихся параметров.

Групповые тесты BE-08 (test_visual_model.py) уже покрывают несколько входов сразу на day-calm;
здесь добавлены одиночные пары на всех трёх днях.
"""
from __future__ import annotations

import copy

import pytest

from app.visual_model import build_visual
from conftest import FIXTURE_NAMES, load_fixture

# Вход -> параметры, которые по таблице он должен менять.
INPUT_TO_PARAMS = {
    "time_of_day": {"light.direction_deg", "line.trajectory"},                 # R-LIGHT-01, R-LINE-01
    "brightness": {"light.intensity", "texture.grain"},                        # R-LIGHT-02, R-TEX-02
    "tempo": {"texture.blur", "motion.reveal_ms", "motion.pulse_ms"},          # R-TEX-03, R-MOT-01, R-MOT-02
}


def _flat(d: dict, prefix: str = "") -> dict:
    out = {}
    for k, v in d.items():
        if isinstance(v, dict):
            out.update(_flat(v, f"{prefix}{k}."))
        else:
            out[f"{prefix}{k}"] = v
    return out


def _changed(a: dict, b: dict) -> set[str]:
    fa, fb = _flat(a), _flat(b)
    return {k for k in fa if fa[k] != fb[k]}


def _alternative(input_name: str, profile: dict) -> tuple[str, str, object]:
    """Возвращает (раздел, поле, новое значение). Новое значение всегда меняет все параметры входа."""
    if input_name == "time_of_day":
        cur = profile["text"]["time_of_day"]
        return "text", "time_of_day", "evening" if cur == "night" else "night"  # направление и траектория разные
    if input_name == "brightness":
        cur = profile["photos"]["brightness"]
        return "photos", "brightness", 0.1 if cur > 0.5 else 0.9
    if input_name == "tempo":
        cur = profile["music"]["tempo_bpm"]
        # 70 даёт blur 0.6, 140 даёт blur 0.1: blur меняется в обе стороны.
        return "music", "tempo_bpm", 70 if (cur is None or cur >= 80) else 140
    raise KeyError(input_name)


@pytest.mark.parametrize("day", FIXTURE_NAMES)
@pytest.mark.parametrize("input_name", list(INPUT_TO_PARAMS))
def test_single_input_changes_only_its_params(day, input_name):
    base_profile = load_fixture(day)["profile"]
    section, key, new_value = _alternative(input_name, base_profile)
    other_profile = copy.deepcopy(base_profile)
    other_profile[section][key] = new_value

    base, _ = build_visual(base_profile, 1, "c")
    other, _ = build_visual(other_profile, 1, "c")

    assert _changed(base, other) == INPUT_TO_PARAMS[input_name], (day, input_name, section, key, new_value)
