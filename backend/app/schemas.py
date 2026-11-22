"""Pydantic-схемы: нормализованный вход и ответы API."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class MusicInput(BaseModel):
    """Музыкальные метаданные, введённые пользователем (ничего не скачиваем)."""

    model_config = ConfigDict(frozen=True)

    url: str = Field(max_length=500)
    description: str = Field(min_length=1, max_length=300)
    title: str | None = Field(default=None, max_length=200)
    artist: str | None = Field(default=None, max_length=200)
    year: int | None = Field(default=None, ge=1900)
    genre: str | None = Field(default=None, max_length=40)
    tempo_bpm: float | None = Field(default=None, ge=40, le=220)
    energy: float | None = Field(default=None, ge=0, le=1)
    mode: Literal["major", "minor", "unknown"] = "unknown"


class DayInput(BaseModel):
    """Проверенный вход POST /api/days (без байтов фото)."""

    model_config = ConfigDict(frozen=True)

    text: str = Field(min_length=1, max_length=5000)
    date: str  # YYYY-MM-DD
    music: MusicInput
    weather: Literal["rain", "fog", "cloud", "sun"] | None = None  # выбор пользователя, без внешних API
    place: str | None = Field(default=None, max_length=80)  # место вручную, без геолокации


class DaySummary(BaseModel):
    id: str
    title: str
    date: str
    preview_url: str | None
    # Для мини-открыток в архиве (необязательные, добавлены без изменения прежних полей).
    folder: str | None = None
    place: str | None = None
    photos: list[str] = []
    visual: dict[str, Any] | None = None


class DayRecord(BaseModel):
    id: str
    title: str
    date: str
    folder: str | None = None  # имя папки дня на диске (для старых дней — прежний формат)
    text: str
    photos: list[str]
    music: dict[str, Any]
    visual: dict[str, Any]
    explain: list[dict[str, Any]]
    profile: dict[str, Any]
