"""При ошибке во время записи не остаётся ни папки, ни записи в БД."""
from __future__ import annotations

import sqlite3

import pytest
from fastapi.testclient import TestClient

from app import storage as storage_module
from app.main import create_app
from app.storage import NewDay, Storage
from conftest import post_day


def new_day() -> NewDay:
    return NewDay(
        date="2026-11-14", title="Вечер, чай и дождь", text="текст",
        music={"url": "https://example.com"}, profile={"photos": {"count": 1}},
        visual={"seed": 1}, explain=[], photos=[b"\xff\xd8jpeg-bytes", b"\xff\xd8more"],
    )


def tree(root):
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and p.suffix != ".sqlite3")


def row_count(storage: Storage) -> int:
    with sqlite3.connect(storage.db_path) as conn:
        return conn.execute("SELECT COUNT(*) FROM days").fetchone()[0]


def test_success_leaves_no_tmp(tmp_path):
    storage = Storage(tmp_path)
    day_id = storage.create_day(new_day())
    assert row_count(storage) == 1
    assert list(storage.tmp_dir.iterdir()) == []
    assert storage.get_day(day_id)["title"] == "Вечер, чай и дождь"


def test_failure_while_writing_files(tmp_path, monkeypatch):
    storage = Storage(tmp_path)
    original = Storage._write_day_files

    def broken(self, root, day_id, day, created_at):
        original(self, root, day_id, day, created_at)  # файлы уже частично записаны
        raise OSError("disk full")

    monkeypatch.setattr(Storage, "_write_day_files", broken)
    with pytest.raises(OSError):
        storage.create_day(new_day())
    assert list(storage.tmp_dir.iterdir()) == []
    assert list(storage.days_dir.iterdir()) == []
    assert row_count(storage) == 0


def test_failure_after_rename_removes_final_folder(tmp_path, monkeypatch):
    storage = Storage(tmp_path)
    storage._ensure()

    class BrokenConnection:
        def execute(self, *a, **k):
            raise sqlite3.OperationalError("database is locked")

        def commit(self):
            raise AssertionError("commit не должен вызываться")

        def rollback(self):
            pass

        def close(self):
            pass

    monkeypatch.setattr(Storage, "_connect", lambda self: BrokenConnection())
    with pytest.raises(sqlite3.OperationalError):
        storage.create_day(new_day())
    assert list(storage.days_dir.iterdir()) == []
    assert list(storage.tmp_dir.iterdir()) == []
    monkeypatch.undo()
    assert row_count(storage) == 0


def test_failure_on_commit_removes_final_folder(tmp_path, monkeypatch):
    storage = Storage(tmp_path)
    storage._ensure()
    real_connect = Storage._connect

    class CommitFails:
        def __init__(self, conn):
            self.conn = conn

        def execute(self, *a, **k):
            return self.conn.execute(*a, **k)

        def commit(self):
            raise sqlite3.OperationalError("commit failed")

        def rollback(self):
            self.conn.rollback()

        def close(self):
            self.conn.close()

    monkeypatch.setattr(Storage, "_connect", lambda self: CommitFails(real_connect(self)))
    with pytest.raises(sqlite3.OperationalError):
        storage.create_day(new_day())
    assert list(storage.days_dir.iterdir()) == []
    assert list(storage.tmp_dir.iterdir()) == []
    monkeypatch.undo()
    assert row_count(storage) == 0


def test_failure_on_rename_cleans_tmp(tmp_path, monkeypatch):
    storage = Storage(tmp_path)
    storage._ensure()

    def broken_rename(self, target):
        raise PermissionError("locked")

    monkeypatch.setattr(storage_module.Path, "rename", broken_rename)
    with pytest.raises(PermissionError):
        storage.create_day(new_day())
    monkeypatch.undo()
    assert list(storage.tmp_dir.iterdir()) == []
    assert list(storage.days_dir.iterdir()) == []
    assert row_count(storage) == 0


def test_api_failure_returns_500_without_trace_and_leaves_nothing(settings, monkeypatch):
    client = TestClient(create_app(settings), raise_server_exceptions=False)

    def broken(self, root, day_id, day, created_at):
        (root / "photos").mkdir(parents=True)
        (root / "photos" / "photo-1.jpg").write_bytes(b"partial")
        raise RuntimeError("boom with secret details")

    monkeypatch.setattr(Storage, "_write_day_files", broken)
    resp = post_day(client)
    assert resp.status_code == 500
    assert resp.json() == {"error": "internal_error"}
    assert "boom" not in resp.text and "Traceback" not in resp.text
    monkeypatch.undo()

    storage = Storage(settings.data_dir)
    assert list(storage.days_dir.iterdir()) == []
    assert list(storage.tmp_dir.iterdir()) == []
    assert client.get("/api/days").json() == []
    assert tree(settings.data_dir) == []
