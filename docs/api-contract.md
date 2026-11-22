# TEAM-02 — контракт VisualModel и таблица «признак → параметр» (v1, черновик)

**Статус:** предложение для согласования Beks и Nivaro. Блокирует FE-04, FE-06 и BE-06. Числа в диапазонах — стартовые, их можно поправить на этапе тестов, но структуру и имена полей меняем только по договорённости.
**Репозиторий:** NivaroCodes/lumen-diary. Этот файл после согласования переносится в `docs/api-contract.md` и `docs/mapping.md`.

---

## 1. Принципы

1. **Детерминированность.** Одинаковые входы дают одинаковую модель. Случайности нет. Seed считается из хешей входов.
2. **Два уровня.** Сначала входы приводятся к `DayProfile` (нормализованные признаки). Потом из `DayProfile` считается `VisualModel` (параметры). Фронтенд получает только `VisualModel` и `explain`, сырые входы он не видит.
3. **Объяснимость.** Каждый параметр в `VisualModel` имеет запись в `explain` с источником, правилом и текстом для «Почему так».
4. **Неизвестное не выдаём за измерение.** Если признак не удалось определить, ставим нейтральное значение и помечаем `"unknown"`. Пользователь видит пометку в карте связей.
5. **Фиксированное не входит в модель.** Сетка, шрифты, позиция даты, заголовка, рамки и линии дня — константы фронтенда. В модели только переменные параметры.

## 2. DayProfile (вход в движок)

```json
{
  "text": {
    "time_of_day": "morning | day | evening | night | unknown",
    "season": "autumn | winter | spring | summer | unknown",
    "environment": "nature | city | home | mixed | unknown",
    "weather": "rain | fog | sun | snow | none | unknown",
    "events_count": 0,
    "length_words": 0,
    "keywords": ["string"]
  },
  "photos": {
    "count": 1,
    "dominant_colors": ["#RRGGBB"],
    "brightness": 0.0,
    "contrast": 0.0,
    "warmth": 0.0
  },
  "music": {
    "source": "link | file",
    "url": "https://... | null",
    "title": "string | null",
    "artist": "string | null",
    "year": 2000,
    "genre": "string | unknown",
    "tempo_bpm": 120,
    "energy": 0.0,
    "mode": "major | minor | unknown",
    "provenance": "entered | measured"
  }
}
```

Правила для `DayProfile`:

- `events_count` — число отдельных событий в тексте, оценка по глаголам действия и разделителям. Ноль — допустимо.
- `brightness`, `contrast`, `warmth` — нормированы в 0.0–1.0 по Pillow-статистике. `warmth` — отношение красного к синему в доминирующих цветах.
- `tempo_bpm` — число или `null`. `null` означает, что темп не указан, и тогда линия и проявка используют нейтральное значение.
- `energy` — 0.0–1.0 или `null`. В MVP берётся из описания пользователя (`provenance: entered`).
- `mode` — в MVP только `unknown` или введённое пользователем. Оценку лада по аудио не делаем до Cloud.

## 3. VisualModel (выход движка, вход фронтенда)

```json
{
  "schema_version": "1.0",
  "seed": 1234567890,
  "light": {
    "direction_deg": 90,
    "intensity": 0.6,
    "temperature_k": 4200
  },
  "palette": {
    "colors": ["#D9B98C", "#4F5D6B", "#F2E8D5"],
    "saturation": 0.5
  },
  "density": {
    "value": 0.4,
    "elements": 6
  },
  "texture": {
    "grain": 0.3,
    "blur": 0.2,
    "weather": "none | rain | fog"
  },
  "line": {
    "trajectory": "rising | falling | flat | wave",
    "amplitude": 0.4,
    "roughness": 0.3,
    "color_index": 0
  },
  "motion": {
    "reveal_ms": 2400,
    "pulse_ms": 1200
  },
  "contrast": 0.5,
  "caption": "string, 3–7 слов"
}
```

Диапазоны и значения по умолчанию:

| Поле | Диапазон | Значение по умолчанию (если входа нет) |
|---|---|---|
| `light.direction_deg` | 0–360 | 90 |
| `light.intensity` | 0.0–1.0 | 0.5 |
| `light.temperature_k` | 2700–6500 | 4500 |
| `palette.colors` | 3–5 hex | `#D9D2C5`, `#8A8F98`, `#2F3440` |
| `palette.saturation` | 0.0–1.0 | 0.4 |
| `density.value` | 0.0–1.0 | 0.3 |
| `density.elements` | 1–12 | 4 |
| `texture.grain` | 0.0–1.0 | 0.2 |
| `texture.blur` | 0.0–1.0 | 0.1 |
| `line.amplitude` | 0.0–1.0 | 0.3 |
| `line.roughness` | 0.0–1.0 | 0.2 |
| `motion.reveal_ms` | 800–4000 | 2400 |
| `motion.pulse_ms` | 600–2400 | 1400 |
| `contrast` | 0.0–1.0 | 0.5 |

Значения по умолчанию совпадают с нейтральным состоянием. Если входа нет, это видно в `explain` как `unknown`.

## 4. Таблица «признак → параметр» (правила)

Правила нумеруются и используются в `explain`. Каждое правило — отдельная строка в коде, покрытая тестом.

| ID | Признак | Параметр | Правило (v1) |
|---|---|---|---|
| R-LIGHT-01 | `text.time_of_day` | `light.direction_deg` | morning → 90; day → 180; evening → 270; night → 0 (сверху); unknown → 90 |
| R-LIGHT-02 | `photos.brightness` | `light.intensity` | intensity = 0.2 + 0.7 × brightness |
| R-LIGHT-03 | `photos.warmth` | `light.temperature_k` | temperature = 6500 − 3800 × warmth |
| R-PAL-01 | `photos.dominant_colors` | `palette.colors` | до 5 доминирующих цветов, отсортированы по доле; при одном фото берём первые 3 |
| R-PAL-02 | `photos.contrast` | `palette.saturation` | saturation = 0.3 + 0.4 × contrast |
| R-DEN-01 | `text.events_count`, `text.length_words` | `density.value` | value = min(1, 0.1 × events_count + length_words / 300) |
| R-DEN-02 | `density.value` | `density.elements` | elements = round(2 + 10 × value) |
| R-TEX-01 | `text.weather` | `texture.weather` | rain → rain; fog → fog; иначе none |
| R-TEX-02 | `photos.brightness` | `texture.grain` | grain = 0.5 × (1 − brightness) |
| R-TEX-03 | `music.tempo_bpm` | `texture.blur` | blur = 0.6 при tempo < 80, 0.3 при 80–110, 0.1 при > 110; null → 0.1 |
| R-LINE-01 | `text.time_of_day` | `line.trajectory` | morning → rising; day → wave; evening → falling; night → flat; unknown → wave |
| R-LINE-02 | `music.energy` | `line.amplitude` | amplitude = 0.1 + 0.8 × energy; null → 0.3 |
| R-LINE-03 | `music.energy`, `music.genre` | `line.roughness` | roughness = 0.2 + 0.5 × energy; жанр rock/electronic добавляет +0.1 (с ограничением 1.0) |
| R-LINE-04 | входы целиком | `line.color_index` | всегда 0 (первый цвет палитры), чтобы линия узнавалась |
| R-MOT-01 | `music.tempo_bpm` | `motion.reveal_ms` | reveal = clamp(4000 − 15 × tempo, 800, 4000); null → 2400 |
| R-MOT-02 | `music.tempo_bpm` | `motion.pulse_ms` | pulse = clamp(round(60000 / tempo), 600, 2400); null → 1400 |
| R-CON-01 | `photos.contrast`, `music.mode` | `contrast` | contrast = 0.3 + 0.4 × photos.contrast; +0.1 при mode = minor; −0.05 при mode = major; clamp 0–1 |
| R-SEED-01 | все входы | `seed` | seed = первые 4 байта SHA-256 (uint32, big-endian, 0…4294967295) от канонизированного JSON входов (текст, хеши фото, ссылка и описание музыки). Дробные значения округляются до 2 знаков half-up |

**Обоснование выбора:** свет связан со временем суток, потому что это прямой признак атмосферы. Палитра берётся из фото, поэтому цвет дня всегда узнаваем. Ритм и амплитуда линии — из музыки. Объяснение каждого правила одинаковое для всех дней.

## 5. Структура explain (для карты связей «Почему так»)

```json
[
  {
    "param": "light.direction_deg",
    "value": 90,
    "rule": "R-LIGHT-01",
    "source": "text.time_of_day",
    "input": "morning",
    "text_ru": "Утро в тексте — свет слева, как в раннее время.",
    "provenance": "measured"
  },
  {
    "param": "line.amplitude",
    "value": 0.46,
    "rule": "R-LINE-02",
    "source": "music.energy",
    "input": 0.45,
    "text_ru": "Энергия песни (оценена по описанию или выбрана) задаёт размах линии.",
    "provenance": "entered"
  }
]
```

Правила для `explain`:

- Каждый параметр из раздела 3 имеет хотя бы одну запись.
- Поле `provenance` берётся из `DayProfile`. Если значение введено пользователем, в тексте об этом сказано явно.
- `text_ru` пишем вручную для каждого правила, без автоматического перевода.
- Фронтенд рисует линии от элемента к источнику по полю `source`. Элемент, которому нет источника, в карте не рисуется.

## 6. API (сводка для docs/api-contract.md)

| Метод | Путь | Вход | Ответ |
|---|---|---|---|
| GET | `/health` | — | `{ "status": "ok" }` |
| POST | `/api/days` | multipart: `text`, `photos[]` (1–5), `music_url` (`music_file` не в MVP), `music_description`, `music_title`, `music_artist`, `music_year`, `music_genre` (ambient, pop, rock, electronic, jazz, classical, hip-hop, folk, other, unknown), `music_tempo_bpm`, `music_energy`, `music_mode`, `date` (необязательно, `YYYY-MM-DD`, по умолчанию сегодня) | `201` + полная запись |
| GET | `/api/days` | `?sort=date_desc` | массив: `id`, `title`, `date`, `preview_url` |
| GET | `/api/days/{id}` | — | `id`, `title`, `date`, `text`, `photos[]`, `music`, `visual`, `explain`, `profile` |

Ошибки: `400` для валидации входов, `413` для слишком большого файла, `404` для отсутствующего дня, `500` с кодом без трейса.

Ошибка валидации — объект `{ "error": "code", "field": "text", "message": "..." }`.

## 6.1. Конфигурация (переменные окружения, см. `.env.example` в корне репозитория)

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `CORS_ORIGIN` | `http://localhost:5173` | Разрешённый origin фронтенда |
| `DATA_DIR` | `./data` | База и папки дней |
| `MAX_UPLOAD_MB` | `10` | Размер одного фото |
| `MAX_PHOTOS` | `5` | Максимум фото в дне |

## 7. Что нужно согласовать (решения на сегодня)

1. Структура `VisualModel` и `DayProfile`, в том числе поля `provenance`.
2. Значения по умолчанию из раздела 3.
3. Правила R-LIGHT-01…R-SEED-01. Можно упростить, но не удалять — без них `explain` не заполнить.
4. Формат `explain` и правило, что элементы без источника не рисуем.
5. Поля музыки в MVP: `music_tempo_bpm` и `music_energy` вводятся пользователем. Если пользователь не вводит, используем `null` и нейтральные значения.

## 8. Проверка контракта

- Фикстуры: три JSON в `backend/tests/fixtures/` (тихий вечер, энергичное утро, плотный день). Используются только для автотестов backend. Фронтенд и демо работают с реальным API, фикстуры в интерфейсе не используются.
- Тест BE-08: одинаковый вход даёт одинаковый seed и `VisualModel`.
- Тест BE-08: изменение только `music_tempo_bpm` меняет только `motion.*`, `texture.blur`.
- Тест BE-08: изменение только фото меняет только `palette.*`, `light.intensity`, `light.temperature_k`, `texture.grain`.
- Тест BE-08: изменение только текста меняет только `light.direction_deg`, `density.*`, `texture.weather`, `line.trajectory`.
