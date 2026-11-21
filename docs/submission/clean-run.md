# Чистый запуск backend (TEAM-06, часть backend)

Проверка выполнена на отдельной копии `origin/main` (коммит `66be948`) во временной папке. Рабочая копия репозитория не использовалась, `data/` в репозитории не менялся.

## Окружение

- ОС: Windows 11 Home 10.0.26300, оболочка Git Bash и PowerShell.
- Python: 3.11.9 (`python.exe` из `Python311`, venv создан заново).
- Пакеты из `backend/requirements.txt` и `backend/requirements-dev.txt`: FastAPI 0.165.0, Pydantic 2.14.4, Pillow 13.0.0, NumPy 2.4.6, uvicorn 0.54.0, python-multipart 0.0.34, pytest 9.2.0, httpx 0.28.1. Установка прошла без ошибок.

## Команды

```bash
git clone --branch main https://github.com/NivaroCodes/lumen-diary.git <temp>/repo
python -m venv <temp>/venv
<temp>/venv/Scripts/python.exe -m pip install -r backend/requirements.txt -r backend/requirements-dev.txt
cd backend
<temp>/venv/Scripts/python.exe -m pytest -q
DATA_DIR=<temp>/data <temp>/venv/Scripts/python.exe -m uvicorn app.main:app --port 8011
```

Запросы выполнялись из Python через `httpx` (не `curl`), текст с кириллицей отправлялся корректно. Скрипт проверки лежит вне репозитория.

## Тесты

`python -m pytest -q` в `backend/`: **220 passed**, 1 предупреждение (`StarletteDeprecationWarning` от `starlette.testclient`, на результат не влияет).

## Запросы к серверу

| Запрос | Код | Результат |
|---|---|---|
| `GET /health` | 200 | `{"status": "ok"}` |
| `POST /api/days` — день `day-calm` | 201 | название «Вечер, комнате и дождь» |
| `POST /api/days` — день `day-dense` | 201 | название «День, совещания и туман» |
| `POST /api/days` — день `day-energy` | 201 | название «Утро, город и солнце» |
| `GET /api/days?sort=date_desc` | 200 | 3 записи, названия совпадают с POST |
| `GET /api/days/{id}` (×3) | 200 | названия совпадают с POST и со списком |
| `POST /api/days` — пустой `text` | 400 | `validation_error`, поле `text` |
| `POST /api/days` — не изображение в `photos` | 400 | `validation_error`, поле `photos` |
| `GET /api/days/no-such-id` | 404 | `not_found` |

В логе сервера нет исключений и ответов 500. Папки дней созданы по схеме `<дата>_<id8>`: `2026-11-14_6e152284`, `2026-11-16_aea8ea96`, `2026-11-15_c62bc7ac`.

## Что не проверялось здесь

- Фронтенд и запуск с одного origin (BE-09) — вне этой проверки. Сервер запускался отдельно, как описано в `backend/README.md`.
- Сохранность данных после перезапуска сервера: проверено на уровне тестов `test_persistence.py`, отдельного перезапуска с этими данными не делалось.
- Скриншоты и открытки — FE-08 (Beks).
