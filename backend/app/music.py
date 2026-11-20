"""Музыкальный вход (BE-05): только метаданные, которые ввёл пользователь.

Никаких запросов к музыкальным сервисам и анализа аудио: ссылка не скачивается.
"""
from __future__ import annotations

from typing import Any

from .schemas import MusicInput


def build_music_profile(music: MusicInput) -> dict[str, Any]:
    """Раздел music из DayProfile. music_description сюда не попадает."""
    return {
        "source": "link",
        "url": music.url,
        "title": music.title,
        "artist": music.artist,
        "year": music.year,
        "genre": music.genre or "unknown",
        "tempo_bpm": _number_or_none(music.tempo_bpm),
        "energy": _number_or_none(music.energy),
        "mode": music.mode,
        "provenance": "entered",
    }


def build_music_record(music: MusicInput, profile_music: dict[str, Any]) -> dict[str, Any]:
    """Музыка в ответе API и в entry.json: профиль плюс описание пользователя.

    Поля type и description совпадают с фикстурами (fixtures/day-*.json).
    """
    return {"type": "link", "description": music.description, **profile_music}


def _number_or_none(value: float | None) -> float | int | None:
    if value is None:
        return None
    return int(value) if float(value).is_integer() else value
