"""Конфигурация сервера из переменных окружения."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CORS_ORIGIN = "http://localhost:5173"


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} должно быть целым числом, получено {raw!r}") from exc
    if value < 1:
        raise ValueError(f"{name} должно быть больше нуля")
    return value


@dataclass(frozen=True)
class Settings:
    cors_origin: str = DEFAULT_CORS_ORIGIN
    data_dir: Path = Path("./data")
    max_upload_mb: int = 10
    max_photos: int = 5

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


def load_settings() -> Settings:
    """Читает окружение при каждом вызове (важно для тестов)."""
    return Settings(
        cors_origin=os.environ.get("CORS_ORIGIN") or DEFAULT_CORS_ORIGIN,
        data_dir=Path(os.environ.get("DATA_DIR") or "./data"),
        max_upload_mb=_int_env("MAX_UPLOAD_MB", 10),
        max_photos=_int_env("MAX_PHOTOS", 5),
    )
