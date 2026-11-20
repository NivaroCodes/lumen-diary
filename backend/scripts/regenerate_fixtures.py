"""Пересобирает tests/fixtures/day-*.json из tests/fixtures/raw/<имя>/.

В raw/<имя>/ лежат input.json (id, date, text, music) и photo-N.png.
Текст и фото проходят через боевой конвейер (text_analysis, photo_analysis,
build_visual), в фикстуры пишутся profile, visual и explain.

Запуск из backend/: python scripts/regenerate_fixtures.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.routes_days import _process_day  # noqa: E402
from app.schemas import DayInput, MusicInput  # noqa: E402
from app.validation import PhotoBlob  # noqa: E402

FIXTURES_DIR = ROOT / "tests" / "fixtures"
RAW_DIR = FIXTURES_DIR / "raw"


def build_fixture(raw: Path) -> dict:
    spec = json.loads((raw / "input.json").read_text(encoding="utf-8"))
    m = spec["music"]
    photo_files = sorted(raw.glob("photo-*.png"), key=lambda p: int(p.stem.split("-")[1]))
    blobs = [PhotoBlob(p.name, "image/png", p.read_bytes()) for p in photo_files]
    day = _process_day(
        DayInput(text=spec["text"], date=spec["date"], music=MusicInput(**m)), blobs
    )
    return {
        "id": spec["id"],
        "title": day.title,
        "date": spec["date"],
        "text": spec["text"],
        "photos": [f"/media/{spec['id']}/photo-{i}.jpg" for i in range(1, len(blobs) + 1)],
        "music": {"type": "link", "url": m["url"], "description": m["description"], "provenance": "entered"},
        "visual": day.visual,
        "explain": day.explain,
        "profile": day.profile,
    }


def build_all() -> dict[str, dict]:
    return {raw.name: build_fixture(raw) for raw in sorted(RAW_DIR.iterdir()) if raw.is_dir()}


def render(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def main() -> None:
    for name, data in build_all().items():
        path = FIXTURES_DIR / f"{name}.json"
        text = render(data)
        if not path.exists() or path.read_bytes() != text.encode("utf-8"):
            path.write_bytes(text.encode("utf-8"))
            print(f"updated {path.name}")
        else:
            print(f"unchanged {path.name}")


if __name__ == "__main__":
    main()
