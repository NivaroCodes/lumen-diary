"""Один порт: FastAPI отдаёт API и собранный фронтенд (SPA fallback, защита от path traversal).

Фронтенд здесь не нужен: временная папка dist создаётся через tmp_path.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

INDEX_HTML = "<!doctype html><html><body><div id=root>LUMEN-INDEX</div></body></html>"
SECRET = "TOP-SECRET-OUTSIDE-DIST"


@pytest.fixture
def dist(tmp_path):
    root = tmp_path / "dist"
    (root / "assets").mkdir(parents=True)
    (root / "index.html").write_text(INDEX_HTML, encoding="utf-8")
    (root / "assets" / "app.js").write_text("console.log('app')", encoding="utf-8")
    (root / "favicon.svg").write_text("<svg></svg>", encoding="utf-8")
    # Файл вне dist: в tmp_path, рядом с dist. Traversal не должен его отдать.
    (tmp_path / "secret.txt").write_text(SECRET, encoding="utf-8")
    return root


@pytest.fixture
def single_origin(tmp_path, dist) -> TestClient:
    settings = Settings(data_dir=tmp_path / "data")
    return TestClient(create_app(settings, frontend_dist=dist))


@pytest.fixture
def no_dist_client(tmp_path) -> TestClient:
    settings = Settings(data_dir=tmp_path / "data")
    return TestClient(create_app(settings, frontend_dist=tmp_path / "missing-dist"))


def test_root_serves_index_html(single_origin):
    resp = single_origin.get("/")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/html")
    assert "LUMEN-INDEX" in resp.text


def test_spa_routes_serve_index_html(single_origin):
    assert "LUMEN-INDEX" in single_origin.get("/archive").text
    assert single_origin.get("/archive").headers["content-type"].startswith("text/html")
    resp = single_origin.get("/memory/abc123")
    assert resp.status_code == 200
    assert "LUMEN-INDEX" in resp.text


def test_static_files_from_dist_are_served(single_origin):
    js = single_origin.get("/assets/app.js")
    assert js.status_code == 200
    assert "console.log" in js.text
    assert single_origin.get("/favicon.svg").status_code == 200


def test_api_and_health_work_with_dist(single_origin):
    assert single_origin.get("/health").json() == {"status": "ok"}
    resp = single_origin.get("/api/days")
    assert resp.status_code == 200
    assert resp.json() == []


def test_unknown_api_paths_are_not_spa_fallback(single_origin):
    for path in ("/api/nope", "/media/unknown", "/health/extra", "/docs/nope"):
        resp = single_origin.get(path)
        assert resp.status_code == 404, path
        assert resp.json() == {"error": "not_found"}, path


def test_openapi_and_docs_are_still_served(single_origin):
    assert single_origin.get("/openapi.json").status_code == 200
    assert single_origin.get("/docs").status_code == 200


@pytest.mark.parametrize("path", [
    "/%2e%2e/secret.txt",
    "/%2e%2e/%2e%2e/etc/passwd",
    "/..%2Fsecret.txt",
    "/assets/..%2F..%2Fsecret.txt",
    "/%2E%2E%5Csecret.txt",
])
def test_path_traversal_does_not_leak_files(single_origin, path):
    resp = single_origin.get(path)
    assert SECRET not in resp.text
    assert resp.status_code == 404


def test_missing_dist_root_returns_hint_and_api_still_works(no_dist_client):
    resp = no_dist_client.get("/")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/json")
    body = resp.json()
    assert body["frontend"] == "not_built"
    assert "npm run build" in body["message"]

    assert no_dist_client.get("/health").json() == {"status": "ok"}
    assert no_dist_client.get("/api/days").status_code == 200


def test_missing_dist_other_paths_are_404_json(no_dist_client):
    resp = no_dist_client.get("/archive")
    assert resp.status_code == 404
    assert resp.json() == {"error": "not_found"}


def test_media_openapi_describes_jpeg_and_not_found(single_origin):
    spec = single_origin.get("/openapi.json").json()
    responses = spec["paths"]["/media/{day_id}/{filename}"]["get"]["responses"]
    assert set(responses["200"]["content"]) == {"image/jpeg"}
    assert responses["404"]["content"]["application/json"]["example"] == {"error": "not_found"}
