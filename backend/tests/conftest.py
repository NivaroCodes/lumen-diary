"""Общие фикстуры: временный DATA_DIR, клиент, синтетические фото."""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402

FIXTURES_DIR = Path(__file__).parent / "fixtures"
FIXTURE_NAMES = ["day-calm", "day-energy", "day-dense"]


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES_DIR / f"{name}.json").read_text(encoding="utf-8"))


def make_image(color=(120, 120, 120), size=(64, 48), fmt="PNG", **save_kwargs) -> bytes:
    """Синтетическое фото: однотонная картинка. Личные снимки в тестах не используем."""
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format=fmt, **save_kwargs)
    return buf.getvalue()


CONTENT_TYPES = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp"}


def photo_part(data: bytes, name="photo.png", content_type="image/png"):
    return ("photos", (name, data, content_type))


def base_fields(**overrides) -> dict:
    fields = {
        "text": "Вечером шёл дождь. Заварила чай и села у окна.",
        "music_url": "https://example.com/song",
        "music_description": "медленная композиция",
    }
    fields.update(overrides)
    return {k: v for k, v in fields.items() if v is not None}


def post_day(client: TestClient, fields: dict | None = None, photos: list | None = None):
    data = base_fields() if fields is None else fields
    files = [photo_part(make_image())] if photos is None else photos
    return client.post("/api/days", data=data, files=files)


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(data_dir=tmp_path / "data")


@pytest.fixture
def client(settings) -> TestClient:
    return TestClient(create_app(settings))
