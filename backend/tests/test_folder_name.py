"""Имена папок дней: build_folder_name и коллизии."""
from __future__ import annotations

from app.storage import NewDay, Storage, build_folder_name

DAY_ID = "6e152284-aaaa-bbbb-cccc-000000000000"


def test_plain_title():
    assert build_folder_name("2026-11-14", "Вечер, комнате и дождь", DAY_ID) == "2026-11-14 Вечер, комнате и дождь"


def test_empty_title_gets_default_and_suffix():
    assert build_folder_name("2026-11-14", "", DAY_ID) == "2026-11-14 День 6e1522"
    assert build_folder_name("2026-11-14", " ?:* ", DAY_ID) == "2026-11-14 День 6e1522"


def test_forbidden_chars_removed_and_spaces_collapsed():
    name = build_folder_name("2026-11-14", 'Вечер: дождь/туман?', DAY_ID)
    assert name == "2026-11-14 Вечер дождь туман"
    assert not any(c in name[10:] for c in '<>:"/\\|?*')
    assert build_folder_name("2026-11-14", "a\x00b\tc", DAY_ID) == "2026-11-14 a b c"


def test_long_title_cut_at_word_boundary():
    title = " ".join(["слово"] * 30)
    name = build_folder_name("2026-11-14", title, DAY_ID)
    part = name[len("2026-11-14 "):]
    assert len(part) <= 80
    assert set(part.split()) == {"слово"}


def test_trailing_dots_and_spaces_stripped():
    assert build_folder_name("2026-11-14", "Дождь... ", DAY_ID) == "2026-11-14 Дождь"


def test_reserved_name_gets_suffix():
    assert build_folder_name("2026-11-14", "con", DAY_ID) == "2026-11-14 con 6e1522"
    assert build_folder_name("2026-11-14", "LPT1", DAY_ID) == "2026-11-14 LPT1 6e1522"


def _day(title="Тот же день") -> NewDay:
    return NewDay(date="2026-11-14", title=title, text="t", music={}, profile={"photos": {"count": 0}},
                  visual={}, explain=[], photos=[])


def test_collisions_get_numeric_suffix(tmp_path):
    storage = Storage(tmp_path)
    ids = [storage.create_day(_day()) for _ in range(3)]
    names = sorted(p.name for p in storage.days_dir.iterdir())
    assert names == ["2026-11-14 Тот же день", "2026-11-14 Тот же день (2)", "2026-11-14 Тот же день (3)"]
    assert [storage.get_day(i)["folder"] for i in ids] == [
        "2026-11-14 Тот же день", "2026-11-14 Тот же день (2)", "2026-11-14 Тот же день (3)"]
