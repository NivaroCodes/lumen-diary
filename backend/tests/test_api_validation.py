from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from conftest import base_fields, make_image, photo_part, post_day


def assert_validation(resp, field, status=400, error="validation_error"):
    assert resp.status_code == status, resp.text
    body = resp.json()
    assert body["error"] == error
    assert body["field"] == field
    assert body["message"]
    assert "Traceback" not in resp.text


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_valid_minimal_request_is_created(client):
    assert post_day(client).status_code == 201


@pytest.mark.parametrize("text", ["", "   \n\t "])
def test_empty_text(client, text):
    assert_validation(post_day(client, base_fields(text=text)), "text")


def test_missing_text(client):
    assert_validation(post_day(client, base_fields(text=None)), "text")


def test_text_too_long(client):
    assert_validation(post_day(client, base_fields(text="а" * 5001)), "text")


def test_text_5000_ok_after_strip(client):
    assert post_day(client, base_fields(text="  " + "а" * 5000 + "  ")).status_code == 201


def test_no_photos(client):
    assert_validation(post_day(client, photos=[]), "photos")


def test_six_photos(client):
    photos = [photo_part(make_image((i * 30, 0, 0))) for i in range(6)]
    assert_validation(post_day(client, photos=photos), "photos")


def test_five_photos_ok(client):
    photos = [photo_part(make_image((i * 30, 0, 0))) for i in range(5)]
    resp = post_day(client, photos=photos)
    assert resp.status_code == 201
    assert len(resp.json()["photos"]) == 5


def test_photos_bracket_field_name_accepted(client):
    resp = post_day(client, photos=[("photos[]", ("a.png", make_image(), "image/png"))])
    assert resp.status_code == 201


def test_wrong_content_type(client):
    photos = [photo_part(make_image(), "a.txt", "text/plain")]
    assert_validation(post_day(client, photos=photos), "photos")


def test_wrong_real_format_with_image_content_type(client):
    gif = make_image(fmt="GIF")
    assert_validation(post_day(client, photos=[photo_part(gif, "a.png", "image/png")]), "photos")


def test_text_file_pretending_to_be_image(client):
    photos = [photo_part(b"this is not an image", "a.jpg", "image/jpeg")]
    assert_validation(post_day(client, photos=photos), "photos")


def test_corrupt_truncated_image(client):
    data = make_image(size=(400, 400), fmt="JPEG")
    photos = [photo_part(data[: len(data) // 2], "a.jpg", "image/jpeg")]
    assert_validation(post_day(client, photos=photos), "photos")


def test_empty_file(client):
    assert_validation(post_day(client, photos=[photo_part(b"", "a.png", "image/png")]), "photos")


def test_file_too_large_gives_413(settings):
    small = Settings(data_dir=settings.data_dir, max_upload_mb=1)
    client = TestClient(create_app(small))
    big = b"\x89PNG\r\n\x1a\n" + b"0" * (1024 * 1024 + 10)
    resp = post_day(client, photos=[photo_part(big)])
    assert resp.status_code == 413
    assert resp.json()["error"] == "file_too_large"
    assert resp.json()["field"] == "photos"
    assert "Traceback" not in resp.text
    assert not (small.data_dir / "days").exists() or not any((small.data_dir / "days").iterdir())


@pytest.mark.parametrize("url", [
    "", "not a url", "ftp://example.com/x", "javascript:alert(1)", "http://", "example.com/song",
    "https://exa mple.com", "file:///etc/passwd",
])
def test_bad_music_url(client, url):
    assert_validation(post_day(client, base_fields(music_url=url)), "music_url")


def test_music_url_too_long(client):
    assert_validation(post_day(client, base_fields(music_url="https://a.com/" + "x" * 490)), "music_url")


def test_missing_music_url(client):
    assert_validation(post_day(client, base_fields(music_url=None)), "music_url")


def test_missing_and_long_music_description(client):
    assert_validation(post_day(client, base_fields(music_description=None)), "music_description")
    assert_validation(post_day(client, base_fields(music_description="  ")), "music_description")
    assert_validation(post_day(client, base_fields(music_description="я" * 301)), "music_description")


@pytest.mark.parametrize("year", ["1899", str(date.today().year + 1), "abc", "20.5"])
def test_year_out_of_range(client, year):
    assert_validation(post_day(client, base_fields(music_year=year)), "music_year")


def test_year_bounds_ok(client):
    assert post_day(client, base_fields(music_year="1900")).status_code == 201
    assert post_day(client, base_fields(music_year=str(date.today().year))).status_code == 201


@pytest.mark.parametrize("field,value", [
    ("music_tempo_bpm", "39"), ("music_tempo_bpm", "221"), ("music_tempo_bpm", "fast"),
    ("music_tempo_bpm", "nan"), ("music_energy", "1.1"), ("music_energy", "-0.1"),
    ("music_energy", "high"), ("music_mode", "dorian"), ("music_genre", "x" * 41), ("music_genre", "dubstep"),
    ("music_title", "x" * 201), ("music_artist", "x" * 201), ("date", "2026-13-40"), ("date", "14.11.2026"),
])
def test_other_field_errors(client, field, value):
    assert_validation(post_day(client, base_fields(**{field: value})), field)


def test_optional_fields_accepted_and_normalised(client):
    resp = post_day(client, base_fields(
        music_title="Название", music_artist="Исполнитель", music_year="2016", music_genre="Ambient",
        music_tempo_bpm="68", music_energy="0.25", music_mode="minor", date="2026-11-14"))
    assert resp.status_code == 201
    music = resp.json()["music"]
    assert music["genre"] == "ambient"
    assert music["tempo_bpm"] == 68
    assert music["energy"] == 0.25
    assert music["mode"] == "minor"
    assert music["provenance"] == "entered"
    assert resp.json()["date"] == "2026-11-14"


def test_invalid_requests_leave_no_data(client, settings):
    post_day(client, base_fields(text=""))
    post_day(client, base_fields(music_url="ftp://x"))
    assert client.get("/api/days").json() == []
    days = settings.data_dir / "days"
    assert not days.exists() or not any(days.iterdir())


def test_unknown_sort_is_400(client):
    assert_validation(client.get("/api/days?sort=bogus"), "sort")
