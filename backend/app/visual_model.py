"""DayProfile -> VisualModel + explain по таблице docs/mapping.md (правила R-*).

Функция build_visual чистая и детерминированная: одинаковый профиль, seed и
caption дают одинаковый результат.
"""
from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Sequence

SCHEMA_VERSION = "1.0"
DEFAULT_PALETTE = ["#D9D2C5", "#8A8F98", "#2F3440"]

DIRECTION = {"morning": 90, "day": 180, "evening": 270, "night": 0}
TRAJECTORY = {"morning": "rising", "day": "wave", "evening": "falling", "night": "flat"}
ROUGH_GENRES = {"rock", "electronic"}


def _round2(x: float) -> float:
    """Два знака после запятой обычным round(): так посчитаны фикстуры (0.445 -> 0.44)."""
    return round(x, 2)


def _round_int(x: float) -> int:
    return int(math.floor(x + 0.5))


def _clamp(x: float, lo: float, hi: float) -> float:
    return min(hi, max(lo, x))


def compute_seed(text: str, photo_hashes: Sequence[str], music_url: str, music_description: str) -> int:
    """R-SEED-01: первые 8 байт SHA-256 от канонизированного JSON входов."""
    canonical = json.dumps(
        {
            "text": text,
            "photos": list(photo_hashes),
            "music_url": music_url,
            "music_description": music_description,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return int.from_bytes(hashlib.sha256(canonical.encode("utf-8")).digest()[:8], "big")


def _prov(value: Any, source_provenance: str) -> str:
    """Происхождение значения: неизвестное не выдаём за измерение."""
    return "unknown" if value is None or value == "unknown" else source_provenance


def build_visual(profile: dict[str, Any], seed: int, caption: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Возвращает (visual, explain)."""
    text, photos, music = profile["text"], profile["photos"], profile["music"]
    explain: list[dict[str, Any]] = []
    music_prov = music.get("provenance", "entered")

    def add(param: str, value: Any, rule: str, source: str, inp: Any, text_ru: str, provenance: str) -> None:
        explain.append(
            {"param": param, "value": value, "rule": rule, "source": source,
             "input": inp, "text_ru": text_ru, "provenance": provenance}
        )

    # --- свет ---
    tod = text.get("time_of_day", "unknown")
    direction = DIRECTION.get(tod, 90)
    add("light.direction_deg", direction, "R-LIGHT-01", "text.time_of_day", tod,
        {"morning": "Утро в тексте задаёт направление света, как у раннего солнца.",
         "day": "День в тексте — свет почти сверху, как в полдень.",
         "evening": "Вечер в тексте — свет с противоположной стороны, как на закате.",
         "night": "Ночь в тексте — свет сверху, как от лампы или луны."}.get(
            tod, "Время суток в тексте не найдено, поэтому свет нейтральный."),
        _prov(tod, "measured"))

    brightness = photos["brightness"]
    intensity = _round2(0.2 + 0.7 * brightness)
    add("light.intensity", intensity, "R-LIGHT-02", "photos.brightness", brightness,
        "Светлые фото делают свет ярче." if brightness >= 0.6
        else "Тёмные фото делают свет приглушённым." if brightness < 0.4
        else "Средняя яркость фото даёт ровный свет.", "measured")

    warmth = photos["warmth"]
    temperature = _round_int(6500 - 3800 * warmth)
    add("light.temperature_k", temperature, "R-LIGHT-03", "photos.warmth", warmth,
        "Тёплые цвета фото задают тёплую температуру света." if warmth >= 0.6
        else "Холодные цвета фото задают холодную температуру света." if warmth < 0.4
        else "Нейтральные цвета фото дают нейтральную температуру света.", "measured")

    # --- палитра ---
    source_colors = list(photos.get("dominant_colors") or [])
    colors = source_colors[:3] if photos.get("count", 1) == 1 else source_colors[:5]
    padded = False
    for fallback in DEFAULT_PALETTE:  # контракт требует 3–5 цветов
        if len(colors) >= 3:
            break
        if fallback not in colors:
            colors.append(fallback)
            padded = True
    add("palette.colors", colors, "R-PAL-01", "photos.dominant_colors", source_colors,
        "Цвета взяты из доминирующих цветов фото"
        + ("; недостающие добавлены из нейтральной палитры." if padded else "."), "measured")

    p_contrast = photos["contrast"]
    saturation = _round2(0.3 + 0.4 * p_contrast)
    add("palette.saturation", saturation, "R-PAL-02", "photos.contrast", p_contrast,
        "Сильный контраст фото даёт насыщенные цвета." if p_contrast >= 0.6
        else "Умеренный контраст фото даёт сдержанную насыщенность." if p_contrast >= 0.3
        else "Мягкий контраст фото даёт приглушённые цвета.", "measured")

    # --- плотность ---
    events, words = text.get("events_count", 0), text.get("length_words", 0)
    density = _round2(min(1.0, 0.1 * events + words / 300))
    elements = int(_clamp(_round_int(2 + 10 * density), 1, 12))
    add("density.value", density, "R-DEN-01", "text.events_count", events,
        f"В тексте событий: {events}, слов: {words}. "
        + ("Много событий — композиция плотная." if density >= 0.7
           else "Немного событий — композиция разреженная." if density < 0.4
           else "Событий умеренно — плотность средняя."), "measured")
    add("density.elements", elements, "R-DEN-02", "density.value", density,
        "Много элементов — композиция насыщена." if elements >= 8
        else "Мало элементов — больше пустого пространства.", "measured")

    # --- фактура ---
    weather = text.get("weather", "none")
    tex_weather = weather if weather in ("rain", "fog") else "none"
    add("texture.weather", tex_weather, "R-TEX-01", "text.weather", weather,
        {"rain": "Дождь в тексте добавляет вертикальную фактуру.",
         "fog": "Туман в тексте добавляет дымку."}.get(tex_weather, "Заметной погоды в тексте нет, фактура без осадков."),
        _prov(weather, "measured"))

    grain = _round2(0.5 * (1 - brightness))
    add("texture.grain", grain, "R-TEX-02", "photos.brightness", brightness,
        "Тёмные фото получают больше зерна." if brightness < 0.5 else "Светлые фото получают меньше зерна.",
        "measured")

    tempo = music.get("tempo_bpm")
    tempo = None if tempo is None or tempo <= 0 else tempo
    blur = 0.1 if tempo is None else 0.6 if tempo < 80 else 0.3 if tempo <= 110 else 0.1
    add("texture.blur", blur, "R-TEX-03", "music.tempo_bpm", tempo,
        {0.6: "Медленный темп песни, введённый вами, делает изображение мягче.",
         0.3: "Средний темп песни, введённый вами, даёт умеренную мягкость."}.get(blur, (
            "Темп не указан, поэтому изображение остаётся чётким." if tempo is None
            else "Быстрый темп песни, введённый вами, оставляет изображение чётким.")),
        _prov(tempo, music_prov))

    # --- линия ---
    trajectory = TRAJECTORY.get(tod, "wave")
    add("line.trajectory", trajectory, "R-LINE-01", "text.time_of_day", tod,
        {"rising": "Утро — линия идёт вверх, день только начинается.",
         "falling": "Вечер — линия идёт вниз, как день к концу.",
         "flat": "Ночь — линия ровная и спокойная."}.get(trajectory, "День или время суток не определено — линия волнистая."),
        _prov(tod, "measured"))

    energy = music.get("energy")
    amplitude = 0.3 if energy is None else _round2(0.1 + 0.8 * energy)
    add("line.amplitude", amplitude, "R-LINE-02", "music.energy", energy,
        "Энергия песни не указана, размах линии нейтральный." if energy is None
        else "Высокая энергия песни, введённая вами, задаёт большой размах линии." if energy >= 0.6
        else "Низкая энергия песни, введённая вами, задаёт небольшой размах линии." if energy < 0.4
        else "Средняя энергия песни, введённая вами, задаёт средний размах линии.",
        _prov(energy, music_prov))

    genre = (music.get("genre") or "unknown").lower()
    roughness = 0.2 + 0.5 * (energy or 0.0) + (0.1 if genre in ROUGH_GENRES else 0.0)
    roughness = _round2(_clamp(roughness, 0.0, 1.0))
    rough_genre = genre in ROUGH_GENRES
    add("line.roughness", roughness, "R-LINE-03",
        "music.genre" if rough_genre else "music.energy", genre if rough_genre else energy,
        "Жанр, введённый вами, и энергия песни делают линию резче." if rough_genre
        else "Энергия песни не указана, линия остаётся гладкой." if energy is None
        else "Спокойная музыка даёт гладкую линию." if energy < 0.4
        else "Энергия песни, введённая вами, добавляет линии шероховатость.",
        music_prov if rough_genre else _prov(energy, music_prov))

    add("line.color_index", 0, "R-LINE-04", "system", None,
        "Линия всегда берёт первый цвет палитры, чтобы узнаваться в каждом дне.", "measured")

    # --- движение ---
    reveal = 2400 if tempo is None else _round_int(_clamp(4000 - 15 * tempo, 800, 4000))
    pulse = 1400 if tempo is None else _round_int(_clamp(_round_int(60000 / tempo), 600, 2400))
    add("motion.reveal_ms", reveal, "R-MOT-01", "music.tempo_bpm", tempo,
        "Темп не указан, проявка идёт с обычной скоростью." if tempo is None
        else "Медленный темп — длинная проявка." if reveal >= 2800
        else "Быстрый темп — короткая проявка." if reveal <= 2200
        else "Средний темп — проявка средней длины.", _prov(tempo, music_prov))
    add("motion.pulse_ms", pulse, "R-MOT-02", "music.tempo_bpm", tempo,
        "Темп не указан, пульс обычный." if tempo is None
        else "Пульс движения соответствует темпу песни.", _prov(tempo, music_prov))

    # --- контраст ---
    mode = music.get("mode", "unknown")
    contrast = 0.3 + 0.4 * p_contrast + (0.1 if mode == "minor" else -0.05 if mode == "major" else 0.0)
    contrast = _round2(_clamp(contrast, 0.0, 1.0))
    add("contrast", contrast, "R-CON-01", "music.mode", mode,
        {"minor": "Минорный лад, введённый вами, добавляет контраст к контрасту фото.",
         "major": "Мажорный лад, введённый вами, слегка смягчает контраст фото."}.get(
            mode, "Лад не указан, контраст задаёт только фото."),
        music_prov if mode in ("minor", "major") else "measured")

    visual = {
        "schema_version": SCHEMA_VERSION,
        "seed": seed,
        "light": {"direction_deg": direction, "intensity": intensity, "temperature_k": temperature},
        "palette": {"colors": colors, "saturation": saturation},
        "density": {"value": density, "elements": elements},
        "texture": {"grain": grain, "blur": blur, "weather": tex_weather},
        "line": {"trajectory": trajectory, "amplitude": amplitude, "roughness": roughness, "color_index": 0},
        "motion": {"reveal_ms": reveal, "pulse_ms": pulse},
        "contrast": contrast,
        "caption": caption,
    }
    return visual, explain
