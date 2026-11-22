"""Разбор текста дня по небольшим словарям и сборка названия (BE-03).

Всё детерминировано: никаких моделей, случайности и внешних запросов.
Совпадение слова со словарём — по началу слова (основе). Основа с суффиксом «$»
требует точного совпадения слова.
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Any

FALLBACK_TITLE = "Обычный день в записи"

_WORD_RE = re.compile(r"[a-zа-яё]+(?:-[a-zа-яё]+)*")
_SENTENCE_RE = re.compile(r"[.!?…\n]+")

TIME_OF_DAY: dict[str, tuple[str, ...]] = {
    "morning": ("утр", "рассвет", "завтрак", "проснул"),
    "day": ("день$", "днем", "днями$", "дневн", "полдень", "обед", "полдн"),
    "evening": ("вечер", "закат", "сумерк"),
    "night": ("ноч", "полночь", "полуночи"),
}

SEASON: dict[str, tuple[str, ...]] = {
    "spring": ("весн", "март", "апрел", "мая$", "май$", "подснежник"),
    "summer": ("лето", "летн", "лета$", "летом$", "июн", "июл", "август", "жар", "жарк"),
    "autumn": ("осен", "сентябр", "октябр", "ноябр", "листопад"),
    "winter": ("зим", "декабр", "январ", "феврал", "мороз"),
}

NATURE = (
    "лес", "парк", "мор", "гор$", "горы$", "горах$", "дерев", "река$", "реке$", "речк",
    "озер", "поле$", "полях$", "луг", "сад$", "саду$", "трав", "цвет", "птиц", "природ",
    "пляж", "берег", "облак", "небо$", "неба$", "небе$",
)
CITY = (
    "улиц", "метро$", "трамва", "офис", "город", "автобус", "площад", "проспект",
    "центр", "магазин", "кафе$", "остановк", "пробк", "вокзал", "работ", "совещан",
)
HOME = ("дом$", "дома$", "домой$", "доме$", "квартир", "окно$", "окна$", "окне$", "окну$", "кухн", "чай", "диван", "комнат")

WEATHER: dict[str, tuple[str, ...]] = {
    "rain": ("дожд", "ливен", "ливн", "морос", "лужи$", "лужа$"),
    "fog": ("туман", "дымк"),
    "snow": ("снег", "снеж", "метел", "сугроб"),
    "sun": ("солнц", "солнеч", "ясн", "безоблачн"),
    "cloud": ("пасмур", "облачн", "облак", "серо"),
}
_WEATHER_ORDER = ("rain", "fog", "snow", "sun", "cloud")

# Основы глаголов действия (прошедшее время и инфинитивы), небольшой список.
ACTION_VERBS = (
    "пошл", "пошё", "пошел", "шёл", "шел", "шла", "шли", "выпил", "заварил", "села", "сел$", "сели$",
    "читал", "позвонил", "позвони", "встрети", "приш", "ушл", "ушё", "ушел", "купил", "сделал",
    "поехал", "поеха", "работал", "гулял", "готовил", "приготов", "написал", "отправил", "убрал",
    "поговорил", "увидел", "позавтрак", "пообедал", "поужинал", "ходил", "ходила", "бегал",
    "побегал", "занимал", "учил", "выучил", "посмотрел", "послушал", "играл", "нарисовал",
    "помог", "забрал", "принёс", "принес", "вернул", "встал", "встала", "проснул", "уехал",
    "приех", "доехал", "зашёл", "зашел", "заходил", "погулял", "съел", "сходил", "провёл",
    "провел", "собрал", "решил", "начал", "закончил", "сидел", "сидела", "ждал", "ждала",
)

STOPWORDS = frozenset(
    """
    это этот эта эти того тому этом очень просто потом тоже также когда если чтобы только уже
    ещё еще было была были будет будто почти всё все всех весь вся себя себе меня мне мной
    нам нас наш наша наши они она оно его него неё нее них там тут здесь куда откуда который
    которая которые какой какая какие свой своя свои один одна одно два две три или либо
    даже лишь чем что как так для при про над под без через между после перед около
    сегодня вчера завтра день дня дни утро вечер ночь утром вечером ночью днем днём
    """.split()
)

_VERB_ENDINGS = ("ла", "ли", "лась", "лись", "лся", "ться", "ть", "тся", "ешь", "ишь", "ет", "ут", "ют", "ят")

# Нейтральные слова для дополнения короткого названия — по сезону.
NEUTRAL_WORDS: dict[str, tuple[str, ...]] = {
    "spring": ("весна", "тишина"),
    "summer": ("лето", "тишина"),
    "autumn": ("осень", "тишина"),
    "winter": ("зима", "тишина"),
    "unknown": ("тишина", "день"),
}

# Слова, которые нельзя ставить в название: прилагательные в косвенных падежах,
# служебные и общие слова. Название «Вечер, ясной и солнце» появилось из-за них.
TITLE_BLOCKLIST = frozenset({
    "пасмурной", "пасмурный", "пасмурно", "пасмурная", "облачной", "облачный", "облачно", "облачная", "серой", "серый", "серая",
    "ясной", "ясная", "ясный", "ясно", "ясного", "ясную", "ясным", "ясные", "ясных",
    "деталей", "детали", "детал", "дела", "дело", "погода", "погоды", "погоде",
    "день", "дня", "дню", "днём", "вечера", "вечером", "утра", "утром", "ночи", "ночью",
    "было", "была", "были", "стало", "очень", "просто", "потом", "вместе", "сегодня",
    "раз", "раза", "время", "времени",
    "отсидел", "отсидела", "отсидели",
    # Наречия, местоимения, оценочные прилагательные и разговорная лексика.
    "ничего", "особенного", "особенно", "тихий", "тихая", "тихо", "громко", "грустно",
    "нормально", "короче", "много", "почти", "долго", "рано", "поздно", "хорошо",
    "тепло", "тёплой", "тёплая", "солнечная", "солнечной", "солнечные", "слишком",
    "совсем", "всего", "весь", "чилил", "лол", "кринж", "полный", "полная",
})

# Все основы словарей среды и погоды: слово, которое по ним совпало, считается «проверенным».
DICTIONARY_STEMS = NATURE + CITY + HOME + tuple(s for stems in WEATHER.values() for s in stems)
_LATIN_RE = re.compile(r"[a-z]")

TIME_TITLE = {"morning": "Утро", "day": "День", "evening": "Вечер", "night": "Ночь"}
WEATHER_TITLE = {"rain": "дождь", "fog": "туман", "snow": "снег", "sun": "солнце", "cloud": "облака"}
ENV_TITLE = {"nature": "природа", "city": "город", "home": "дом", "mixed": "прогулка"}



# Ключевое слово в названии приводим к именительному падежу: стем словаря -> слово.
# Нужно, чтобы заголовок читался («Парк и солнце», а не «Парку и солнце»). Стемы, уже
# совпадающие с именительным падежом, тоже перечислены для явности.
TITLE_LEMMAS: dict[str, str] = {
    "лес": "лес", "парк": "парк", "мор": "море", "гор$": "гора", "горы$": "горы",
    "горах$": "горы", "дерев": "деревья", "река$": "река", "реке$": "река", "речк": "речка",
    "озер": "озеро", "поле$": "поле", "полях$": "поля", "луг": "луг", "сад$": "сад",
    "саду$": "сад", "трав": "трава", "цвет": "цветы", "птиц": "птицы", "природ": "природа",
    "пляж": "пляж", "берег": "берег", "облак": "облака", "небо$": "небо", "неба$": "небо", "небе$": "небо",
    "улиц": "улица", "метро$": "метро", "трамва": "трамвай", "офис": "офис", "город": "город",
    "автобус": "автобус", "площад": "площадь", "проспект": "проспект", "центр": "центр",
    "магазин": "магазин", "кафе$": "кафе", "остановк": "остановка", "пробк": "пробки",
    "вокзал": "вокзал", "работ": "работа", "совещан": "совещание",
    "дом$": "дом", "дома$": "дом", "домой$": "дом", "доме$": "дом", "квартир": "квартира",
    "окно$": "окно", "окна$": "окно", "окне$": "окно", "окну$": "окно", "кухн": "кухня",
    "чай": "чай", "диван": "диван", "комнат": "комната",
    "дожд": "дождь", "ливен": "ливень", "ливн": "ливень", "морос": "морось",
    "лужи$": "лужи", "лужа$": "лужа", "туман": "туман", "дымк": "дымка",
    "снег": "снег", "снеж": "снег", "метел": "метель", "сугроб": "сугробы",
    "солнц": "солнце", "солнеч": "солнце", "облачн": "облака", "пасмур": "пасмурно",
}


def _lemma(word: str) -> str:
    """Именительный падеж ключевого слова по словарю. Берём самый длинный подходящий стем."""
    best = None
    for stem in TITLE_LEMMAS:
        if _match(word, (stem,)) and (best is None or len(stem) > len(best)):
            best = stem
    return TITLE_LEMMAS[best] if best else word

def _tokens(text: str) -> list[str]:
    return _WORD_RE.findall(text.lower())


def _match(token: str, stems: tuple[str, ...]) -> bool:
    token = token.replace("ё", "е")  # «ё» и «е» считаем одной буквой
    for stem in (s.replace("ё", "е") for s in stems):
        if stem.endswith("$"):
            if token == stem[:-1]:
                return True
        elif token.startswith(stem):
            return True
    return False


def _count(tokens: list[str], stems: tuple[str, ...]) -> int:
    return sum(1 for t in tokens if _match(t, stems))


def _pick_by_count(
    tokens: list[str], table: dict[str, tuple[str, ...]], order: tuple[str, ...] | None = None
) -> str | None:
    """Ключ с наибольшим числом совпадений. При равенстве — тот, что встретился раньше в тексте."""
    best_key, best_score, best_first = None, 0, 10**9
    for key in order or tuple(table):
        stems = table[key]
        positions = [i for i, t in enumerate(tokens) if _match(t, stems)]
        if not positions:
            continue
        score, first = len(positions), positions[0]
        if score > best_score or (score == best_score and first < best_first):
            best_key, best_score, best_first = key, score, first
    return best_key


def _events_count(text: str) -> int:
    count = 0
    for sentence in _SENTENCE_RE.split(text):
        tokens = _tokens(sentence)
        if any(_match(t, ACTION_VERBS) for t in tokens):
            count += 1
    return max(0, min(12, count))


def _is_verbish(token: str) -> bool:
    return _match(token, ACTION_VERBS) or token.endswith(_VERB_ENDINGS)


def _keywords(tokens: list[str], limit: int = 5) -> list[str]:
    """Сначала слова из словарей среды и погоды (по порядку в тексте), затем частые слова."""
    dictionary_stems = NATURE + CITY + HOME + tuple(s for stems in WEATHER.values() for s in stems)
    result: list[str] = []

    def add(word: str) -> None:
        if word not in result and len(result) < limit:
            result.append(word)

    for t in tokens:
        if len(t) >= 3 and t not in STOPWORDS and _match(t, dictionary_stems):
            add(t)

    freq = Counter(t for t in tokens if len(t) >= 4 and t not in STOPWORDS and not _is_verbish(t))
    first_pos: dict[str, int] = {}
    for i, t in enumerate(tokens):
        first_pos.setdefault(t, i)
    for word in sorted(freq, key=lambda w: (-freq[w], first_pos[w])):
        add(word)
    return result


def analyze_text(text: str) -> dict[str, Any]:
    """Возвращает text-часть DayProfile (раздел 2 контракта)."""
    tokens = _tokens(text)

    time_of_day = _pick_by_count(tokens, TIME_OF_DAY) or "unknown"
    season = _pick_by_count(tokens, SEASON) or "unknown"
    weather = _pick_by_count(tokens, WEATHER, _WEATHER_ORDER) or "none"

    nature, city, home = _count(tokens, NATURE), _count(tokens, CITY), _count(tokens, HOME)
    if nature and city:
        environment = "mixed"
    elif nature:
        environment = "nature"
    elif city:
        environment = "city"
    elif home:
        environment = "home"
    else:
        environment = "unknown"

    return {
        "time_of_day": time_of_day,
        "season": season,
        "environment": environment,
        "weather": weather,
        "events_count": _events_count(text),
        "length_words": len(tokens),
        "keywords": _keywords(tokens),
    }


def make_title(profile: dict[str, Any]) -> str:
    """Название из 3–7 слов: время суток + ключевое слово + погода или среда. Детерминировано."""
    try:
        title = _build_title(profile)
        if 3 <= len(title.split()) <= 7:
            return title
    except Exception:  # название не должно ронять создание дня
        pass
    return FALLBACK_TITLE


def _titleable(word: str, taken: set[str]) -> bool:
    """Слово годится в название: не английское, не занято и не в блок-листе."""
    return word not in taken and word not in TITLE_BLOCKLIST and _LATIN_RE.search(word) is None


def _build_title(profile: dict[str, Any]) -> str:
    time_word = TIME_TITLE.get(profile.get("time_of_day", "unknown"))
    weather_tail = WEATHER_TITLE.get(profile.get("weather"))
    tail = weather_tail or ENV_TITLE.get(profile.get("environment"))
    taken = {w.lower() for w in (time_word, tail) if w}
    raw_keyword = next((k for k in profile.get("keywords") or [] if _titleable(k, taken)), None)
    # Слово из словаря приводим к именительному падежу; свободное слово оставляем как есть.
    keyword = _lemma(raw_keyword) if raw_keyword and _match(raw_keyword, DICTIONARY_STEMS) else raw_keyword

    # Уверенные признаки: время суток, погода или среда, слово из словаря. Свободное слово
    # из текста не считается. Если уверенных меньше двух — нейтральное название, а не случайное слово.
    confident = sum([time_word is not None, tail is not None,
                     raw_keyword is not None and _match(raw_keyword, DICTIONARY_STEMS)])
    if confident < 2:
        return f"{time_word} в записи" if time_word else FALLBACK_TITLE

    if time_word and keyword and tail:
        words = [time_word + ",", keyword, "и", tail]  # «Вечер, чай и дождь»
    else:
        words = [w for w in (time_word, keyword, tail) if w] or ["день"]

    # Короткое название дополняем нейтральным словом по сезону: «Ночь и снег», «Дождь и осень».
    if len(words) == 2:
        words = [words[0], "и", words[1]]
    elif len(words) == 1:
        extra = NEUTRAL_WORDS.get(profile.get("season"), NEUTRAL_WORDS["unknown"])
        words = [words[0], "и", next((w for w in extra if w != words[0].lower()), extra[0])]
    words[0] = words[0][:1].upper() + words[0][1:]
    return " ".join(words)
