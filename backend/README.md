# Lumen Diary — backend

FastAPI-сервер: принимает день (текст, фото, данные о песне), строит `DayProfile`, считает `VisualModel` по правилам R-* и сохраняет день в папку и в SQLite. Всё детерминировано: одинаковые входы дают одинаковый результат. LLM, внешних API и анализа аудио нет.

## Установка и запуск

Нужен Python 3.11. Из папки `backend/`:

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows; на Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Сервер слушает `http://127.0.0.1:8000`. При первом запросе создаются `DATA_DIR/lumen.sqlite3`, `DATA_DIR/days/` и `DATA_DIR/tmp/`.

## Запуск одним портом

FastAPI может отдавать и API, и собранный фронтенд с одного порта. Сначала соберите фронтенд (из корня репозитория):

```bash
cd frontend
npm ci
npm run build          # появится frontend/dist/
cd ../backend
uvicorn app.main:app --port 8000
```

Откройте `http://localhost:8000`. Фронтенд раздаётся из `frontend/dist`; путь вычисляется относительно `backend/app`, поэтому команду можно запускать из любой папки. Неизвестные пути вне `/api`, `/media`, `/health`, `/docs` и `/openapi.json` (например, `/archive`, `/memory/<id>`) возвращают `index.html`. Если `frontend/dist` не собран, API работает как обычно, а `/` отвечает JSON с подсказкой собрать фронтенд.

## Переменные окружения

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `CORS_ORIGIN` | `http://localhost:5173` | Разрешённый origin фронтенда |
| `DATA_DIR` | `./data` | Где лежат база и папки дней (не коммитится) |
| `MAX_UPLOAD_MB` | `10` | Максимальный размер одного фото |
| `MAX_PHOTOS` | `5` | Максимум фото в одном дне |

Образец со всеми переменными — `.env.example` в корне репозитория. Сервер **не читает файл `.env`**: переменные нужно выставить в окружении до запуска, например в PowerShell `$env:DATA_DIR = "D:\lumen-data"`, в bash `export DATA_DIR=./data`. Если переменная не задана, берётся значение по умолчанию из таблицы.

## Эндпоинты

| Метод | Путь | Ответ |
|---|---|---|
| GET | `/health` | `{"status": "ok"}` |
| POST | `/api/days` | `201` + полная запись дня (multipart, поля ниже) |
| GET | `/api/days?sort=date_desc` | `[{id, title, date, preview_url}]`, по дате (новые сверху), при равенстве — по времени создания |
| GET | `/api/days/{id}` | `{id, title, date, text, photos[], music, visual, explain, profile}` |
| GET | `/media/{id}/photo-N.jpg` | Очищенное фото дня (JPEG без EXIF) |

Поля `POST /api/days` (multipart). Обязательные: `text` (1–5000), `photos` или `photos[]` (1–`MAX_PHOTOS` файлов JPEG/PNG/WebP, формат проверяется по содержимому), `music_url` (http/https, до 500), `music_description` (1–300). Файл песни не принимается (`music_file` в MVP нет). Необязательные: `music_title`, `music_artist` (до 200), `music_year` (1900…текущий), `music_genre` (ambient, pop, rock, electronic, jazz, classical, hip-hop, folk, other, unknown; регистр не важен), `music_tempo_bpm` (40…220), `music_energy` (0…1), `music_mode` (`major`/`minor`/`unknown`), `date` (`YYYY-MM-DD`, по умолчанию сегодня). На фронтенде `music_tempo_bpm`, `music_energy` и `music_mode` не вводятся числом: форма оценивает их по `music_description` или по кнопкам «Темп»/«Настроение» (`frontend/src/music-hints.ts`) и передаёт в этих же полях API.

Ошибки: `400 {"error": "validation_error", "field": "...", "message": "..."}`, `413 {"error": "file_too_large", ...}`, `404 {"error": "not_found"}`, `500 {"error": "internal_error"}`. Трассировок в ответах нет. Все ошибки проверки входов имеют код `validation_error`; поле `field` указывает, какой вход неверен.

## Пример POST /api/days

Пример на Python (httpx уже есть в `requirements-dev.txt`). Для кириллицы в тексте используйте Python, а не `curl` в Git Bash: там аргументы передаются в другой кодировке и текст теряется.

```python
import httpx

with open("photo.jpg", "rb") as f:
    files = [("photos", ("photo.jpg", f.read(), "image/jpeg"))]

data = {
    "text": "Утром был в парке, пил кофе и читал книгу. Вечером шёл дождь.",
    "music_url": "https://example.com/track",
    "music_description": "Спокойная песня без слов",
    "music_genre": "ambient",
    "music_energy": "0.3",
    "date": "2026-11-21",  # необязательно, по умолчанию сегодня
}
r = httpx.post("http://127.0.0.1:8000/api/days", data=data, files=files, timeout=60)
print(r.status_code, r.json()["title"])  # 201 и название дня
```

Поля `music_genre`, `music_energy`, `music_tempo_bpm`, `music_mode`, `music_title`, `music_artist`, `music_year` необязательны. Для фото можно передать несколько файлов: повторите пару `("photos", ...)` в списке `files`.

## Список инструментов

Зависимости Python и фронтенда, а также внешние сервисы (которых нет) описаны в [`docs/tools.md`](../docs/tools.md).

## Что лежит на диске

```
DATA_DIR/
  lumen.sqlite3
  days/<YYYY-MM-DD> <название дня>/
    entry.json  profile.json  visual.json  explain.json  memory.json
    photos/photo-1.jpg …
  tmp/            # временные папки при создании, после операции пусто
```

Имя папки — дата и короткое название дня (`build_folder_name` в `app/storage.py`), например `2026-11-14 Вечер, комнате и дождь`. При совпадении имён добавляется суффикс ` (2)`, ` (3)` и т. д. Папки, созданные до этой схемы (формат `<YYYY-MM-DD>_<id8>`), продолжают читаться: путь хранится в записи дня, а не пересчитывается.

День создаётся атомарно: запись во `tmp/<id>`, переименование в папку дня, затем commit в SQLite. При ошибке папки удаляются, записи в БД нет. EXIF (включая GPS) в сохранённые фото не попадает.

## Swagger

Запустите сервер и откройте `http://127.0.0.1:8000/docs` (схема: `/openapi.json`). `POST /api/days` можно попробовать прямо в Swagger.

## Тесты

```bash
cd backend
python -m pytest -q
```

Фикстуры пересобираются: `python scripts/regenerate_fixtures.py` (из `backend/`); тест `test_fixtures_fresh.py` проверяет, что файлы свежие. Тесты пишут только во временные папки (`tmp_path`), фото генерируются синтетически. В `tests/fixtures/` лежат `day-*.json` (генерируются из `tests/fixtures/raw/`).

## Расхождения с контрактом

Контракт (`docs/api-contract.md`, `docs/mapping.md`) не менялся. Найденное:

1. **Нет `visual_model.py` и `test_visual_model.py` в архиве** (только `docs/` и `fixtures/`). Реализация написана по `mapping.md`, оригинала для сверки нет; единственная реализация — `app/visual_model.py`.
2. ~~seed 64-бит~~ Решено: seed — uint32 (4 байта SHA-256), `docs/` обновлены.
3. ~~Округление фикстур~~ Решено: Decimal ROUND_HALF_UP, фикстуры генерируются `scripts/regenerate_fixtures.py` из `tests/fixtures/raw/`, сравнение точное.
5. **`warmth`:** контракт — «отношение красного к синему в доминирующих цветах», задание — `0.5 + (mean R − mean B) / 510` по всем пикселям. Реализована формула из задания.
6. **Форма `music` в ответе не описана в контракте.** Отдаём объединение формы фикстур (`type`, `description`, `url`, `provenance`) и `DayProfile.music` (`source`, `title`, `artist`, `year`, `genre`, `tempo_bpm`, `energy`, `mode`).
7. **Поля `music_description`, `music_mode`, `date` отсутствуют в таблице контракта (раздел 6).** Добавлены по заданию; `date` необязательное, нужно, чтобы дни из фикстур получили свои даты. Контракт перечисляет `music_file`, он не реализован (не в MVP).
8. **Фото отдаются своим маршрутом, а не `StaticFiles`.** URL по заданию `/media/<id>/<file>`, а папка называется `<date> <название>` (раньше `<date>_<id8>`), `StaticFiles` не сопоставит одно с другим. Маршрут принимает только `photo-N.jpg` (защита от выхода из папки). Файлы лежат в `photos/`, а URL без этого сегмента, как в фикстурах.
9. **Палитра:** при менее чем трёх найденных цветах (например, однотонное фото) контракт требует 3–5 цветов. `build_visual` дополняет нейтральной палитрой по умолчанию и пишет об этом в `explain`.
10. **R-LINE-03:** жанр теперь из закрытого списка, бонус `+0.1` — для `rock` и `electronic`.
11. **Погода:** если слов о погоде нет, `weather = "none"` (а не `unknown`), для R-TEX-01 разницы нет.
12. **`CORS_ORIGIN` по умолчанию:** `.env.example` лежит в корне репозитория, значение по умолчанию `http://localhost:5173` выбрано как адрес Vite.

## Известные ограничения

- Размер файла проверяется после того, как Starlette принял multipart-тело (на диск во временный файл): ранней отсечки по `Content-Length` нет.
- Анализ текста — небольшие словари и основы слов, точность намеренно невысокая (воспроизводимость важнее).

## Демо-дни

Три дня с разным настроением (осенний парк, ночь в офисе, дождливое утро), фото нарисованы кодом:

```bash
python scripts/seed_demo_days.py --url http://127.0.0.1:8000
```

Необязательные поля формы: `weather` (`rain`, `fog`, `cloud`, `sun` — выбор пользователя, важнее погоды из текста) и `place` (до 80 символов).
