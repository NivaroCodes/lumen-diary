"""Хранение дней: папка на диске + SQLite (BE-07).

Создание атомарное: пишем во временную папку, переименовываем в папку дня,
затем коммитим запись в БД. При любой ошибке временная и созданная папки
удаляются, записи в БД не остаётся.
"""
from __future__ import annotations

import json
import re
import shutil
import sqlite3
import uuid
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS days (
    id           TEXT PRIMARY KEY,
    date         TEXT NOT NULL,
    title        TEXT NOT NULL,
    folder       TEXT NOT NULL,
    created_at   TEXT NOT NULL,
    text         TEXT NOT NULL,
    music_json   TEXT NOT NULL,
    profile_json TEXT NOT NULL,
    visual_json  TEXT NOT NULL,
    explain_json TEXT NOT NULL
)
"""

PHOTO_NAME = "photo-{}.jpg"


@dataclass(frozen=True)
class NewDay:
    date: str
    title: str
    text: str
    music: dict[str, Any]
    profile: dict[str, Any]
    visual: dict[str, Any]
    explain: list[dict[str, Any]]
    photos: list[bytes]  # очищенные JPEG без EXIF


_FORBIDDEN_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f\x7f]')
_RESERVED_NAMES = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
_MAX_TITLE_LEN = 80
_EMPTY_TITLE = "День"


def _sanitize_title(title: str) -> str:
    clean = _FORBIDDEN_CHARS.sub(" ", title)
    clean = re.sub(r"\s+", " ", clean).strip(" .")
    if len(clean) > _MAX_TITLE_LEN:
        cut = clean[:_MAX_TITLE_LEN]
        # обрезаем по границе слова, если следующий символ не пробел (слово разрезано)
        if clean[_MAX_TITLE_LEN] != " " and " " in cut:
            cut = cut.rsplit(" ", 1)[0]
        clean = cut.rstrip(" .")
    return clean


def build_folder_name(date: str, title: str, day_id: str) -> str:
    """Имя папки дня: ``YYYY-MM-DD <название>``, безопасное для Windows и Linux."""
    clean = _sanitize_title(title)
    suffix = day_id[:6]
    if not clean:
        clean = f"{_EMPTY_TITLE} {suffix}"
    elif clean.split(".")[0].strip().upper() in _RESERVED_NAMES:
        clean = f"{clean} {suffix}"
    return f"{date} {clean}"


def _dump(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)


class Storage:
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self._ready = False

    # --- пути ---
    @property
    def db_path(self) -> Path:
        return self.data_dir / "lumen.sqlite3"

    @property
    def days_dir(self) -> Path:
        return self.data_dir / "days"

    @property
    def tmp_dir(self) -> Path:
        return self.data_dir / "tmp"

    def _ensure(self) -> None:
        if self._ready:
            return
        for d in (self.data_dir, self.days_dir, self.tmp_dir):
            d.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.execute(SCHEMA)
            conn.commit()
        self._ready = True

    def cleanup_tmp(self) -> None:
        """Удаляет остатки незавершённых записей (вызывается при старте приложения)."""
        if self.tmp_dir.is_dir():
            for entry in self.tmp_dir.iterdir():
                shutil.rmtree(entry, ignore_errors=True) if entry.is_dir() else entry.unlink(missing_ok=True)

    def _connect(self) -> sqlite3.Connection:
        self._ensure()
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # --- запись ---
    def _write_day_files(self, root: Path, day_id: str, day: NewDay, created_at: str) -> None:
        (root / "photos").mkdir(parents=True)
        for i, data in enumerate(day.photos, start=1):
            (root / "photos" / PHOTO_NAME.format(i)).write_bytes(data)
        (root / "entry.json").write_text(
            _dump({"id": day_id, "date": day.date, "created_at": created_at, "text": day.text, "music": day.music}),
            encoding="utf-8",
        )
        (root / "profile.json").write_text(_dump(day.profile), encoding="utf-8")
        (root / "visual.json").write_text(_dump(day.visual), encoding="utf-8")
        (root / "explain.json").write_text(_dump(day.explain), encoding="utf-8")
        (root / "memory.json").write_text(
            _dump({"title": day.title, "visual": day.visual, "explain": day.explain}), encoding="utf-8"
        )

    def create_day(self, day: NewDay) -> str:
        """Сохраняет день и возвращает его id."""
        self._ensure()
        day_id = str(uuid.uuid4())
        base_folder = build_folder_name(day.date, day.title, day_id)
        created_at = datetime.now(timezone.utc).isoformat(timespec="microseconds")
        tmp = self.tmp_dir / day_id
        folder = base_folder
        final = self.days_dir / folder
        conn: sqlite3.Connection | None = None
        created = False
        try:
            self._write_day_files(tmp, day_id, day, created_at)
            attempt = 1
            while True:  # коллизия имён: " (2)", " (3)"; существующие папки не трогаем
                if not final.exists():
                    try:
                        tmp.rename(final)
                        created = True
                        break
                    except OSError:
                        if not final.exists():
                            raise
                attempt += 1
                folder = f"{base_folder} ({attempt})"
                final = self.days_dir / folder
            conn = self._connect()
            conn.execute(
                "INSERT INTO days (id, date, title, folder, created_at, text, music_json,"
                " profile_json, visual_json, explain_json) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (day_id, day.date, day.title, folder, created_at, day.text,
                 json.dumps(day.music, ensure_ascii=False), json.dumps(day.profile, ensure_ascii=False),
                 json.dumps(day.visual, ensure_ascii=False), json.dumps(day.explain, ensure_ascii=False)),
            )
            conn.commit()
        except BaseException:
            if conn is not None:
                conn.rollback()
            shutil.rmtree(tmp, ignore_errors=True)
            if created:
                shutil.rmtree(final, ignore_errors=True)
            raise
        finally:
            if conn is not None:
                conn.close()
        return day_id

    # --- чтение ---
    def list_days(self) -> list[dict[str, Any]]:
        with closing(self._connect()) as conn:
            rows = conn.execute(
                "SELECT id, title, date, folder, profile_json, visual_json FROM days"
                " ORDER BY date DESC, created_at DESC"
            ).fetchall()
        return [
            {
                "id": r["id"],
                "title": r["title"],
                "date": r["date"],
                "preview_url": media_url(r["id"], 1) if _photo_count(r["profile_json"]) else None,
                "folder": r["folder"],
                "place": (json.loads(r["profile_json"]).get("context") or {}).get("place"),
                "photos": [media_url(r["id"], i) for i in range(1, _photo_count(r["profile_json"]) + 1)],
                "visual": json.loads(r["visual_json"]),
            }
            for r in rows
        ]

    def get_day(self, day_id: str) -> dict[str, Any] | None:
        with closing(self._connect()) as conn:
            r = conn.execute("SELECT * FROM days WHERE id = ?", (day_id,)).fetchone()
        if r is None:
            return None
        profile = json.loads(r["profile_json"])
        return {
            "id": r["id"],
            "title": r["title"],
            "date": r["date"],
            "folder": r["folder"],
            "text": r["text"],
            "photos": [media_url(r["id"], i) for i in range(1, _photo_count(r["profile_json"]) + 1)],
            "music": json.loads(r["music_json"]),
            "visual": json.loads(r["visual_json"]),
            "explain": json.loads(r["explain_json"]),
            "profile": profile,
        }

    def photo_path(self, day_id: str, filename: str) -> Path | None:
        """Путь к фото дня или None. Принимает только photo-N.jpg (без обхода каталогов)."""
        if not filename.startswith("photo-") or not filename.endswith(".jpg"):
            return None
        number = filename[len("photo-"):-len(".jpg")]
        if not number.isdigit() or str(int(number)) != number:
            return None
        with closing(self._connect()) as conn:
            r = conn.execute("SELECT folder FROM days WHERE id = ?", (day_id,)).fetchone()
        if r is None:
            return None
        path = self.days_dir / r["folder"] / "photos" / filename
        return path if path.is_file() else None


def media_url(day_id: str, index: int) -> str:
    return f"/media/{day_id}/{PHOTO_NAME.format(index)}"


def _photo_count(profile_json: str) -> int:
    return int(json.loads(profile_json).get("photos", {}).get("count", 0))
