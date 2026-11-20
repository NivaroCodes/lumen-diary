"""Создание дней из фикстур, архив, открытие дня, 404."""
from __future__ import annotations

import io
import json

import pytest
from PIL import Image

from app.visual_model import build_visual
from conftest import FIXTURE_NAMES, load_fixture, make_image, photo_part, post_day


def hex_to_rgb(h: str) -> tuple[int, int, int]:
    return int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)


def fixture_request(name: str):
    """Поля и синтетические фото (цвета из палитры фикстуры) для POST /api/days."""
    fx = load_fixture(name)
    music = fx["profile"]["music"]
    fields = {
        "text": fx["text"],
        "date": fx["date"],
        "music_url": music["url"],
        "music_description": fx["music"]["description"],
        "music_year": str(music["year"]),
        "music_genre": music["genre"],
        "music_tempo_bpm": str(music["tempo_bpm"]),
        "music_energy": str(music["energy"]),
        "music_mode": music["mode"],
    }
    photos = [photo_part(make_image(hex_to_rgb(c), (96, 64))) for c in fx["profile"]["photos"]["dominant_colors"]]
    return fx, fields, photos


@pytest.fixture
def three_days(client):
    created = {}
    for name in FIXTURE_NAMES:
        fx, fields, photos = fixture_request(name)
        resp = post_day(client, fields, photos)
        assert resp.status_code == 201, resp.text
        created[name] = resp.json()
    return created


def test_create_returns_full_record(three_days):
    record = three_days["day-calm"]
    assert set(record) == {"id", "title", "date", "text", "photos", "music", "visual", "explain", "profile"}
    assert record["date"] == "2026-11-14"
    assert len(record["photos"]) == 3
    assert 3 <= len(record["title"].split()) <= 7
    assert record["visual"]["caption"] == record["title"]
    assert record["visual"]["schema_version"] == "1.0"


def test_three_folders_named_by_template(three_days, settings):
    folders = sorted(p.name for p in (settings.data_dir / "days").iterdir())
    expected = sorted(f"{d['date']}_{d['id'][:8]}" for d in three_days.values())
    assert folders == expected
    for d in three_days.values():
        root = settings.data_dir / "days" / f"{d['date']}_{d['id'][:8]}"
        assert {p.name for p in root.iterdir()} == {
            "entry.json", "photos", "profile.json", "visual.json", "explain.json", "memory.json"}
        assert sorted(p.name for p in (root / "photos").iterdir()) == [
            f"photo-{i}.jpg" for i in range(1, len(d["photos"]) + 1)]
        memory = json.loads((root / "memory.json").read_text(encoding="utf-8"))
        assert memory == {"title": d["title"], "visual": d["visual"], "explain": d["explain"]}
        entry = json.loads((root / "entry.json").read_text(encoding="utf-8"))
        assert entry["text"] == d["text"] and entry["date"] == d["date"] and entry["music"] == d["music"]
        assert json.loads((root / "visual.json").read_text(encoding="utf-8")) == d["visual"]
        assert json.loads((root / "profile.json").read_text(encoding="utf-8")) == d["profile"]
        assert (root / "tmp").exists() is False
    assert not any((settings.data_dir / "tmp").iterdir())


def test_saved_photos_have_no_exif(three_days, settings):
    for d in three_days.values():
        root = settings.data_dir / "days" / f"{d['date']}_{d['id'][:8]}" / "photos"
        for path in root.iterdir():
            with Image.open(path) as img:
                assert img.format == "JPEG"
                assert len(img.getexif()) == 0


def test_archive_lists_three_days_newest_first(client, three_days):
    items = client.get("/api/days?sort=date_desc").json()
    assert len(items) == 3
    dates = [i["date"] for i in items]
    assert dates == sorted(dates, reverse=True)
    assert {i["id"] for i in items} == {d["id"] for d in three_days.values()}
    for item in items:
        assert set(item) == {"id", "title", "date", "preview_url"}
        assert client.get(item["preview_url"]).status_code == 200


def test_archive_sorted_by_date_desc_then_created_desc(client):
    ids = {}
    for label, day in [("old", "2026-01-01"), ("new_a", "2026-05-05"), ("new_b", "2026-05-05"), ("mid", "2026-03-03")]:
        resp = post_day(client, {**fixture_request("day-calm")[1], "date": day})
        ids[label] = resp.json()["id"]
    order = [i["id"] for i in client.get("/api/days").json()]
    assert order == [ids["new_b"], ids["new_a"], ids["mid"], ids["old"]]


def test_archive_default_sort_and_empty(client):
    assert client.get("/api/days").json() == []


def test_open_day_returns_visual_explain_profile(client, three_days):
    for d in three_days.values():
        got = client.get(f"/api/days/{d['id']}")
        assert got.status_code == 200
        assert got.json() == d


def test_music_driven_params_match_fixture(three_days):
    """Часть visual, зависящая только от музыки, точно совпадает с фикстурой."""
    for name, d in three_days.items():
        fx = load_fixture(name)["visual"]
        v = d["visual"]
        assert v["motion"] == fx["motion"]
        assert v["texture"]["blur"] == fx["texture"]["blur"]
        assert v["line"]["amplitude"] == fx["line"]["amplitude"]
        assert v["line"]["roughness"] == fx["line"]["roughness"]
        assert v["line"]["color_index"] == 0


def test_visual_and_explain_follow_rules_for_stored_profile(three_days):
    for d in three_days.values():
        visual, explain = build_visual(d["profile"], d["visual"]["seed"], d["title"])
        assert d["visual"] == visual
        assert d["explain"] == explain


def test_calm_fixture_text_features(three_days):
    profile = three_days["day-calm"]["profile"]
    assert profile["text"]["time_of_day"] == "evening"
    assert profile["text"]["weather"] == "rain"
    assert three_days["day-calm"]["visual"]["texture"]["weather"] == "rain"
    assert three_days["day-calm"]["visual"]["light"]["direction_deg"] == 270


def test_same_input_same_visual(client):
    _, fields, photos = fixture_request("day-energy")
    a = post_day(client, fields, photos).json()
    b = post_day(client, fields, photos).json()
    assert a["id"] != b["id"]
    assert a["visual"] == b["visual"]
    assert a["explain"] == b["explain"]
    assert a["title"] == b["title"]


def test_different_photo_changes_seed(client):
    _, fields, photos = fixture_request("day-energy")
    other = [photo_part(make_image((1, 2, 3)))]
    assert post_day(client, fields, photos).json()["visual"]["seed"] != post_day(client, fields, other).json()["visual"]["seed"]


def test_music_description_stored_but_not_in_profile(three_days):
    d = three_days["day-energy"]
    assert d["music"]["description"] == "быстрый электронный трек, мажор"
    assert "description" not in d["profile"]["music"]
    assert d["profile"]["music"]["source"] == "link"


def test_open_unknown_day_is_404(client, three_days):
    resp = client.get("/api/days/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404
    assert resp.json() == {"error": "not_found"}
    assert client.get("/api/days/'; DROP TABLE days;--").status_code == 404
    assert len(client.get("/api/days").json()) == 3


def test_media_served_and_unknown_is_404(client, three_days):
    d = three_days["day-dense"]
    resp = client.get(d["photos"][0])
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/jpeg"
    Image.open(io.BytesIO(resp.content)).verify()
    assert client.get(f"/media/{d['id']}/photo-99.jpg").status_code == 404
    assert client.get(f"/media/{d['id']}/entry.json").status_code == 404
    assert client.get(f"/media/{d['id']}/..%2Fentry.json").status_code == 404
    assert client.get("/media/unknown/photo-1.jpg").status_code == 404


def test_cors_header_for_configured_origin(client):
    resp = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert resp.headers["access-control-allow-origin"] == "http://localhost:5173"
