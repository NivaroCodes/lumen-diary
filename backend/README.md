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

## Переменные окружения

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `CORS_ORIGIN` | `http://localhost:5173` | Разрешённый origin фронтенда |
| `DATA_DIR` | `./data` | Где лежат база и папки дней (не коммитится) |
| `MAX_UPLOAD_MB` | `10` | Максимальный размер одного фото |
| `MAX_PHOTOS` | `5` | Максимум фото в одном дне |

## Эндпоинты

| Метод | Путь | Ответ |
|---|---|---|
| GET | `/health` | `{"status": "ok"}` |
| POST | `/api/days` | `201` + полная запись дня (multipart, поля ниже) |
| GET | `/api/days?sort=date_desc` | `[{id, title, date, preview_url}]`, по дате (новые сверху), при равенстве — по времени создания |
| GET | `/api/days/{id}` | `{id, title, date, text, photos[], music, visual, explain, profile}` |
| GET | `/media/{id}/photo-N.jpg` | Очищенное фото дня (JPEG без EXIF) |

Поля `POST /api/days` (multipart): `text` (1–5000), `photos` или `photos[]` (1–`MAX_PHOTOS` файлов JPEG/PNG/WebP, формат проверяется по содержимому), `music_url` (http/https, до 500), `music_description` (1–300); необязательные: `music_title`, `music_artist` (до 200), `music_year` (1900…текущий), `music_genre` (ambient, pop, rock, electronic, jazz, classical, hip-hop, folk, other, unknown; регистр не важен), `music_tempo_bpm` (40…220), `music_energy` (0…1), `music_mode` (`major`/`minor`/`unknown`), `date` (`YYYY-MM-DD`, по умолчанию сегодня).

Ошибки: `400 {"error": "validation_error", "field": "...", "message": "..."}`, `413 {"error": "file_too_large", ...}`, `404 {"error": "not_found"}`, `500 {"error": "internal_error"}`. Трассировок в ответах нет.

## Что лежит на диске

```
DATA_DIR/
  lumen.sqlite3
  days/<YYYY-MM-DD>_<id8>/
    entry.json  profile.json  visual.json  explain.json  memory.json
    photos/photo-1.jpg …
  tmp/            # временные папки при создании, после операции пусто
```

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
8. **Фото отдаются своим маршрутом, а не `StaticFiles`.** URL по заданию `/media/<id>/<file>`, а папка называется `<date>_<id8>`, `StaticFiles` не сопоставит одно с другим. Маршрут принимает только `photo-N.jpg` (защита от выхода из папки). Файлы лежат в `photos/`, а URL без этого сегмента, как в фикстурах.
9. **Палитра:** при менее чем трёх найденных цветах (например, однотонное фото) контракт требует 3–5 цветов. `build_visual` дополняет нейтральной палитрой по умолчанию и пишет об этом в `explain`.
10. **R-LINE-03:** жанр теперь из закрытого списка, бонус `+0.1` — для `rock` и `electronic`.
11. **Погода:** если слов о погоде нет, `weather = "none"` (а не `unknown`), для R-TEX-01 разницы нет.
12. **`CORS_ORIGIN` по умолчанию:** `.env.example` лежит в корне репозитория, значение по умолчанию `http://localhost:5173` выбрано как адрес Vite.

## Известные ограничения

- Размер файла проверяется после того, как Starlette принял multipart-тело (на диск во временный файл): ранней отсечки по `Content-Length` нет.
- Анализ текста — небольшие словари и основы слов, точность намеренно невысокая (воспроизводимость важнее).
