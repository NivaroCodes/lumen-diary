from __future__ import annotations

import io

import numpy as np
import pytest
from PIL import Image

from app.photo_analysis import analyze_photos, kmeans_colors
from conftest import make_image

GPS_IFD = 0x8825


def jpeg_with_gps(color=(90, 120, 200), size=(80, 60)) -> bytes:
    exif = Image.Exif()
    exif[0x010F] = "TestCam"
    exif[GPS_IFD] = {1: "N", 2: (55.0, 45.0, 0.0), 3: "E", 4: (37.0, 37.0, 0.0)}
    return make_image(color, size, fmt="JPEG", exif=exif)


def test_brighter_photo_has_higher_brightness():
    light = analyze_photos([make_image((240, 240, 240))]).profile
    dark = analyze_photos([make_image((20, 20, 20))]).profile
    assert light["brightness"] > dark["brightness"]
    assert 0.9 < light["brightness"] <= 1.0
    assert 0.0 <= dark["brightness"] < 0.1


def test_warmer_photo_has_higher_warmth():
    warm = analyze_photos([make_image((230, 140, 60))]).profile
    cold = analyze_photos([make_image((60, 140, 230))]).profile
    assert warm["warmth"] > 0.5 > cold["warmth"]


def test_warmth_formula():
    # clamp(0.5 + (R - B) / 510)
    assert analyze_photos([make_image((255, 0, 0))]).profile["warmth"] == pytest.approx(1.0)
    assert analyze_photos([make_image((0, 0, 255))]).profile["warmth"] == pytest.approx(0.0)
    assert analyze_photos([make_image((100, 50, 100))]).profile["warmth"] == pytest.approx(0.5)


def test_brightness_formula():
    expected = (0.299 * 200 + 0.587 * 100 + 0.114 * 50) / 255
    got = analyze_photos([make_image((200, 100, 50))]).profile["brightness"]
    assert got == pytest.approx(expected, abs=1e-3)


def test_contrast_flat_vs_split():
    flat = analyze_photos([make_image((128, 128, 128))]).profile["contrast"]
    img = Image.new("RGB", (64, 64), (0, 0, 0))
    img.paste((255, 255, 255), (0, 0, 32, 64))
    buf = io.BytesIO()
    img.save(buf, "PNG")
    split = analyze_photos([buf.getvalue()]).profile["contrast"]
    assert flat == 0.0
    assert split == pytest.approx(127.5 / 128, abs=1e-3)
    assert 0.0 <= split <= 1.0


def test_dominant_colors_sorted_by_share_and_uppercase_hex():
    img = Image.new("RGB", (100, 100), (255, 0, 0))
    img.paste((0, 0, 255), (0, 0, 100, 25))
    img.paste((0, 255, 0), (0, 25, 100, 40))
    buf = io.BytesIO()
    img.save(buf, "PNG")
    colors = analyze_photos([buf.getvalue()]).profile["dominant_colors"]
    assert colors == ["#FF0000", "#0000FF", "#00FF00"]


def test_dominant_colors_at_most_five_and_deterministic():
    rng = np.random.default_rng(3)
    arr = rng.integers(0, 256, (120, 160, 3), dtype=np.uint8)
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, "PNG")
    data = buf.getvalue()
    a = analyze_photos([data]).profile
    b = analyze_photos([data]).profile
    assert a == b
    assert 1 <= len(a["dominant_colors"]) <= 5
    assert all(c.startswith("#") and c == c.upper() and len(c) == 7 for c in a["dominant_colors"])


def test_kmeans_is_deterministic():
    pixels = np.random.default_rng(1).integers(0, 256, (2000, 3)).astype(np.float64)
    assert kmeans_colors(pixels) == kmeans_colors(pixels)


def test_multiple_photos_aggregate():
    result = analyze_photos([make_image((240, 240, 240)), make_image((20, 20, 20))]).profile
    single_light = analyze_photos([make_image((240, 240, 240))]).profile
    single_dark = analyze_photos([make_image((20, 20, 20))]).profile
    assert result["count"] == 2
    assert result["brightness"] == pytest.approx((single_light["brightness"] + single_dark["brightness"]) / 2, abs=1e-3)
    assert set(result["dominant_colors"]) == {"#F0F0F0", "#141414"}


def test_large_image_is_downscaled_for_analysis_but_still_works():
    result = analyze_photos([make_image((10, 200, 10), size=(1500, 1000))])
    assert result.profile["count"] == 1
    with Image.open(io.BytesIO(result.cleaned_jpegs[0])) as stored:
        assert max(stored.size) == 1500  # хранимая копия не больше 1600 px


def test_exif_gps_is_removed_from_stored_copy():
    source = jpeg_with_gps()
    with Image.open(io.BytesIO(source)) as img:
        assert img.getexif().get_ifd(GPS_IFD), "в исходнике должен быть GPS"
        assert img.getexif().get(0x010F) == "TestCam"
    cleaned = analyze_photos([source]).cleaned_jpegs[0]
    with Image.open(io.BytesIO(cleaned)) as img:
        exif = img.getexif()
        assert len(exif) == 0
        assert not exif.get_ifd(GPS_IFD)
        assert "exif" not in img.info
    assert b"Exif" not in cleaned[:64]


def test_exif_orientation_is_applied():
    exif = Image.Exif()
    exif[0x0112] = 6  # повернуть на 90° по часовой
    data = make_image((10, 10, 10), size=(80, 40), fmt="JPEG", exif=exif)
    cleaned = analyze_photos([data]).cleaned_jpegs[0]
    with Image.open(io.BytesIO(cleaned)) as img:
        assert img.size == (40, 80)


def test_png_with_alpha_is_accepted():
    buf = io.BytesIO()
    Image.new("RGBA", (20, 20), (255, 0, 0, 0)).save(buf, "PNG")
    assert analyze_photos([buf.getvalue()]).profile["brightness"] > 0.9  # прозрачное -> белый фон


def test_requires_at_least_one_photo():
    with pytest.raises(ValueError):
        analyze_photos([])
