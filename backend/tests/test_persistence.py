from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app
from conftest import post_day
from test_api_days import fixture_request


def test_day_survives_app_restart(settings):
    first = TestClient(create_app(settings))
    created = []
    for name in ("day-calm", "day-energy", "day-dense"):
        _, fields, photos = fixture_request(name)
        resp = post_day(first, fields, photos)
        assert resp.status_code == 201
        created.append(resp.json())
    archive_before = first.get("/api/days").json()

    second = TestClient(create_app(settings))  # «перезапуск»: новое приложение, тот же DATA_DIR
    assert second.get("/api/days").json() == archive_before
    for day in created:
        got = second.get(f"/api/days/{day['id']}")
        assert got.status_code == 200
        assert got.json() == day
        assert second.get(day["photos"][0]).status_code == 200


def test_app_does_not_touch_disk_until_used(tmp_path):
    from app.config import Settings

    data = tmp_path / "never-created"
    create_app(Settings(data_dir=data))
    assert not data.exists()
