from __future__ import annotations

import pytest

from app.text_analysis import FALLBACK_TITLE, _titleable, analyze_text, make_title


@pytest.mark.parametrize("text,expected", [
    ("Утром пил кофе.", "morning"),
    ("Днём был на работе.", "day"),
    ("Вечером шёл дождь.", "evening"),
    ("Ночью не спалось.", "night"),
    ("Просто текст без примет.", "unknown"),
])
def test_time_of_day(text, expected):
    assert analyze_text(text)["time_of_day"] == expected


def test_time_of_day_majority_wins_and_tie_goes_to_first():
    assert analyze_text("Утром спал. Вечером гулял. Вечером читал.")["time_of_day"] == "evening"
    assert analyze_text("Вечером гулял, потом ночью читал.")["time_of_day"] == "evening"


@pytest.mark.parametrize("text,expected", [
    ("Осенью красиво.", "autumn"), ("Зимой холодно.", "winter"),
    ("Весной тепло.", "spring"), ("Летом жарко.", "summer"), ("Без сезона.", "unknown"),
])
def test_season(text, expected):
    assert analyze_text(text)["season"] == expected


@pytest.mark.parametrize("text,expected", [
    ("Гуляли по лесу и парку.", "nature"),
    ("Ехал в метро по городу.", "city"),
    ("Сидела дома у окна.", "home"),
    ("Из офиса пошёл в парк.", "mixed"),
    ("Думал о разном.", "unknown"),
])
def test_environment(text, expected):
    assert analyze_text(text)["environment"] == expected


@pytest.mark.parametrize("text,expected", [
    ("Шёл дождь.", "rain"), ("Был густой туман.", "fog"),
    ("Выпал снег.", "snow"), ("Светило солнце.", "sun"), ("Ничего особенного.", "none"),
])
def test_weather(text, expected):
    assert analyze_text(text)["weather"] == expected


def test_events_count_counts_sentences_with_action_verbs():
    text = "Заварила чай. Тихо. Позвонила маме! Просто тишина"
    assert analyze_text(text)["events_count"] == 2
    assert analyze_text("Тишина и покой.")["events_count"] == 0


def test_events_count_capped_at_12():
    text = " ".join(["Пошла гулять."] * 30)
    assert analyze_text(text)["events_count"] == 12


def test_length_words():
    assert analyze_text("раз два три четыре")["length_words"] == 4


def test_keywords_limit_and_content():
    text = "Дождь, чай, окно, трамвай, парк, река, лес, метро. Дождь снова."
    keywords = analyze_text(text)["keywords"]
    assert len(keywords) <= 5
    assert keywords[0] == "дождь"
    assert len(set(keywords)) == len(keywords)


def test_analysis_is_deterministic():
    text = "Утром шёл дождь. Заварила чай и села у окна. Позвонила маме."
    assert analyze_text(text) == analyze_text(text)


def test_profile_has_contract_fields():
    assert set(analyze_text("Текст.")) == {
        "time_of_day", "season", "environment", "weather", "events_count", "length_words", "keywords"}


def test_title_has_three_to_seven_words():
    texts = [
        "Вечером шёл дождь. Заварила чай, села у окна.",
        "Ночью шёл снег.",
        "Ок",
        "Дождь.",
        "Просто текст без примет.",
        "Утром трамвай, потом парк и кофе на солнце.",
        "!!!",
    ]
    for text in texts:
        title = make_title(analyze_text(text))
        assert 3 <= len(title.split()) <= 7, (text, title)


def test_title_same_text_same_title():
    text = "Вечером шёл дождь. Заварила чай, села у окна."
    assert make_title(analyze_text(text)) == make_title(analyze_text(text))
    assert make_title(analyze_text(text)) == "Вечер, чай и дождь"


def test_title_pads_short_with_season_word():
    title = make_title(analyze_text("Осенью лил дождь."))
    assert 3 <= len(title.split()) <= 7


def test_title_fallback_on_bad_profile():
    assert make_title({"time_of_day": object(), "keywords": 5}) == FALLBACK_TITLE


def test_title_fallback_when_too_long():
    profile = {"time_of_day": "evening", "weather": "rain", "season": "autumn",
               "keywords": ["один два три четыре пять шесть семь"]}
    assert make_title(profile) == FALLBACK_TITLE


def test_title_skips_adjectives_and_verbs():
    # Регрессия: раньше попадали «ясной», «деталей», «отсидел».
    assert make_title(analyze_text("Просто день без деталей.")) != "День и деталей"
    assert "ясной" not in make_title(analyze_text("Погода была ясной."))
    assert "отсидел" not in make_title(analyze_text("Отсидел 7 уроков. Вечером домашка."))
    assert "деталей" not in make_title(analyze_text("День без деталей, вечером шёл дождь."))


@pytest.mark.parametrize("word", ["школа", "пчела", "стол", "зал", "школе"])
def test_title_keeps_nouns_ending_in_l_or_la(word):
    # Регрессия: суффикс «-л/-ла» из regex по прошедшему времени отсекал существительные.
    assert _titleable(word, set()) is True


def test_title_keeps_school_keyword_in_title():
    title = make_title({"time_of_day": "evening", "keywords": ["школе", "чай"], "weather": "rain"})
    assert "школе" in title
