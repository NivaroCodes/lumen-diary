"""Проверка входов POST /api/days (BE-02)."""
from __future__ import annotations

import io
import math
import warnings
from dataclasses import dataclass
from datetime import date as date_cls
from typing import Any, Mapping
from urllib.parse import urlsplit

from PIL import Image, UnidentifiedImageError
from starlette.datastructures import UploadFile

from .config import Settings
from .errors import ApiError, file_too_large, validation_error
from .schemas import DayInput, MusicInput

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_PIL_FORMATS = {"JPEG", "PNG", "WEBP"}
MAX_TEXT = 5000
MAX_URL = 500
MAX_DESCRIPTION = 300
MAX_META = 200
MAX_GENRE = 40
MIN_YEAR = 1900
MODES = {"major", "minor", "unknown"}


@dataclass(frozen=True)
class PhotoBlob:
    filename: str
    content_type: str
    data: bytes
    too_large: bool = False


async def read_photo(upload: UploadFile, limit: int) -> PhotoBlob:
    """Читает не больше limit+1 байт: этого достаточно, чтобы понять, что файл велик."""
    data = await upload.read(limit + 1)
    too_large = len(data) > limit
    return PhotoBlob(
        filename=upload.filename or "",
        content_type=(upload.content_type or "").split(";")[0].strip().lower(),
        data=b"" if too_large else data,
        too_large=too_large,
    )


def _field(form: Mapping[str, Any], name: str) -> str | None:
    value = form.get(name)
    if value is None or isinstance(value, UploadFile):
        return None
    return str(value)


def _optional(form: Mapping[str, Any], name: str) -> str | None:
    value = _field(form, name)
    if value is None:
        return None
    value = value.strip()
    return value or None


def _number(raw: str, field: str, label: str) -> float:
    try:
        value = float(raw.replace(",", "."))
    except ValueError:
        raise validation_error(field, f"{label}: нужно число") from None
    if not math.isfinite(value):
        raise validation_error(field, f"{label}: нужно конечное число")
    return value


def validate_text(raw: str | None) -> str:
    text = (raw or "").strip()
    if not text:
        raise validation_error("text", "Текст дня обязателен")
    if len(text) > MAX_TEXT:
        raise validation_error("text", f"Текст не длиннее {MAX_TEXT} символов")
    return text


def validate_url(raw: str | None) -> str:
    url = (raw or "").strip()
    if not url:
        raise validation_error("music_url", "Ссылка на музыку обязательна")
    if len(url) > MAX_URL:
        raise validation_error("music_url", f"Ссылка не длиннее {MAX_URL} символов")
    if any(ch.isspace() for ch in url):
        raise validation_error("music_url", "Ссылка не должна содержать пробелов")
    try:
        parts = urlsplit(url)
        host = parts.hostname
    except ValueError:
        raise validation_error("music_url", "Некорректная ссылка") from None
    if parts.scheme not in ("http", "https") or not host:
        raise validation_error("music_url", "Ссылка должна начинаться с http:// или https://")
    return url


def validate_photo(blob: PhotoBlob, index: int, max_mb: int) -> None:
    """Проверяет один файл по содержимому. Бросает ApiError."""
    label = f"Фото {index}"
    if blob.too_large:
        raise file_too_large(f"{label}: размер больше {max_mb} МБ")
    if blob.content_type not in ALLOWED_CONTENT_TYPES:
        raise validation_error("photos", f"{label}: допустимы только JPEG, PNG и WebP")
    if not blob.data:
        raise validation_error("photos", f"{label}: файл пустой")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(blob.data)) as img:
                if img.format not in ALLOWED_PIL_FORMATS:
                    raise validation_error("photos", f"{label}: допустимы только JPEG, PNG и WebP")
                img.load()  # поймает обрезанные и повреждённые файлы
    except ApiError:
        raise
    except (UnidentifiedImageError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise validation_error("photos", f"{label}: файл не является корректным изображением") from None
    except Exception:  # OSError, SyntaxError, ValueError и т. п. от Pillow
        raise validation_error("photos", f"{label}: файл повреждён") from None


def validate_photos(blobs: list[PhotoBlob], settings: Settings) -> None:
    if len(blobs) < 1:
        raise validation_error("photos", "Нужно хотя бы одно фото")
    if len(blobs) > settings.max_photos:
        raise validation_error("photos", f"Не больше {settings.max_photos} фото")
    for i, blob in enumerate(blobs, start=1):
        validate_photo(blob, i, settings.max_upload_mb)


def validate_music(form: Mapping[str, Any]) -> MusicInput:
    url = validate_url(_field(form, "music_url"))

    description = (_field(form, "music_description") or "").strip()
    if not description:
        raise validation_error("music_description", "Описание музыки обязательно")
    if len(description) > MAX_DESCRIPTION:
        raise validation_error("music_description", f"Описание не длиннее {MAX_DESCRIPTION} символов")

    title = _optional(form, "music_title")
    if title and len(title) > MAX_META:
        raise validation_error("music_title", f"Название не длиннее {MAX_META} символов")
    artist = _optional(form, "music_artist")
    if artist and len(artist) > MAX_META:
        raise validation_error("music_artist", f"Исполнитель не длиннее {MAX_META} символов")

    year: int | None = None
    raw_year = _optional(form, "music_year")
    if raw_year is not None:
        try:
            year = int(raw_year)
        except ValueError:
            raise validation_error("music_year", "Год должен быть целым числом") from None
        current = date_cls.today().year
        if not MIN_YEAR <= year <= current:
            raise validation_error("music_year", f"Год должен быть от {MIN_YEAR} до {current}")

    genre = _optional(form, "music_genre")
    if genre is not None:
        genre = genre.lower()
        if len(genre) > MAX_GENRE:
            raise validation_error("music_genre", f"Жанр не длиннее {MAX_GENRE} символов")

    tempo: float | None = None
    raw_tempo = _optional(form, "music_tempo_bpm")
    if raw_tempo is not None:
        tempo = _number(raw_tempo, "music_tempo_bpm", "Темп")
        if not 40 <= tempo <= 220:
            raise validation_error("music_tempo_bpm", "Темп должен быть от 40 до 220 BPM")

    energy: float | None = None
    raw_energy = _optional(form, "music_energy")
    if raw_energy is not None:
        energy = _number(raw_energy, "music_energy", "Энергия")
        if not 0 <= energy <= 1:
            raise validation_error("music_energy", "Энергия должна быть от 0 до 1")

    mode = (_optional(form, "music_mode") or "unknown").lower()
    if mode not in MODES:
        raise validation_error("music_mode", "Лад: major, minor или unknown")

    return MusicInput(
        url=url, description=description, title=title, artist=artist, year=year,
        genre=genre, tempo_bpm=tempo, energy=energy, mode=mode,
    )


def validate_date(raw: str | None) -> str:
    """Необязательное поле date (YYYY-MM-DD). Без него берётся сегодняшняя дата сервера."""
    value = (raw or "").strip()
    if not value:
        return date_cls.today().isoformat()
    try:
        if len(value) != 10:
            raise ValueError
        return date_cls.fromisoformat(value).isoformat()
    except ValueError:
        raise validation_error("date", "Дата должна быть в формате YYYY-MM-DD") from None


def validate_day_form(
    form: Mapping[str, Any], photos: list[PhotoBlob], settings: Settings
) -> DayInput:
    """Порядок проверки: text, photos, music_*, date. Возвращает первую найденную ошибку."""
    text = validate_text(_field(form, "text"))
    validate_photos(photos, settings)
    music = validate_music(form)
    day_date = validate_date(_field(form, "date"))
    return DayInput(text=text, date=day_date, music=music)
