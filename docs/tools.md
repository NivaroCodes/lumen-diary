# Инструменты и библиотеки

Список составлен по файлам репозитория: `backend/requirements.txt`, `backend/requirements-dev.txt`, `frontend/package.json` и импортам в `backend/app/` и `frontend/src/`. Версии Python-зависимостей совпадают с установленными в `backend/.venv` (проверено).

## Backend (Python 3.11)

### Рабочие зависимости (`backend/requirements.txt`)

| Пакет | Версия | Лицензия | Назначение в проекте |
|---|---|---|---|
| FastAPI | 0.165.0 | MIT | HTTP-сервер и маршруты: `app/main.py`, `app/routes_days.py` |
| uvicorn | 0.54.0 | BSD-3-Clause | ASGI-сервер для запуска: `uvicorn app.main:app` |
| Pydantic | 2.14.4 | MIT | Модели входа и ответа: `app/schemas.py` |
| python-multipart | 0.0.34 | Apache-2.0 | Разбор `multipart/form-data` (форма `POST /api/days`), нужен FastAPI для `request.form()` |
| Pillow | 13.0.0 | MIT-CMU (HPND) | Проверка и очистка фото: декодирование, удаление EXIF (`app/validation.py`, `app/photo_analysis.py`) |
| NumPy | 2.4.6 | BSD-3-Clause (с компонентами 0BSD, MIT, Zlib, CC0) | Статистика по пикселям фото: яркость, контраст, тепло, доминирующие цвета (`app/photo_analysis.py`) |

### Для разработки и тестов (`backend/requirements-dev.txt`)

| Пакет | Версия | Лицензия | Назначение |
|---|---|---|---|
| pytest | 9.2.0 | MIT | Запуск тестов: `python -m pytest -q` в папке `backend/` |
| httpx | 0.28.1 | BSD-3-Clause | HTTP-клиент, на котором работает `fastapi.testclient` в `tests/conftest.py`. Также используется в примере из `backend/README.md` |

### Стандартная библиотека Python

| Модуль | Где используется |
|---|---|
| `sqlite3` | База дней: `app/storage.py`, файл `DATA_DIR/lumen.sqlite3` |
| `hashlib` | SHA-256 для `seed` (`app/visual_model.py`) и хешей фото |
| `decimal` | Округление до двух знаков (ROUND_HALF_UP) при генерации фикстур (`scripts/regenerate_fixtures.py`) |
| `urllib.parse` | Проверка ссылки на музыку (`app/validation.py`) |
| `json`, `re`, `collections`, `pathlib`, `datetime`, `dataclasses`, `contextlib` | Служебно: файлы дней, словари слов, пути, даты, данные |

### Внешние сервисы и модели

- **Внешние API не используются.** В `backend/app/` нет HTTP-запросов к внешним адресам; `httpx` в коде приложения не импортируется, только в тестах.
- **AI-модели не используются.** Нет вызовов LLM, `openai`, `anthropic`, `requests`. Анализ текста — словари и основы слов (`app/text_analysis.py`), анализ фото — Pillow и NumPy.
- **Анализ аудио не делается.** Темп, энергию и лад фронтенд оценивает по фразе пользователя о звучании песни (`frontend/src/music-hints.ts`) или берёт из явного выбора; ссылка на песню не скачивается.
- **Демо-дни** (`backend/scripts/seed_demo_days.py`): фото нарисованы кодом через Pillow, чужих снимков нет.

## Frontend (`frontend/package.json`)

Лицензии взяты из `package.json` установленных пакетов (`node_modules/*/package.json`).

### Зависимости времени выполнения

| Пакет | Версия | Лицензия | Где используется |
|---|---|---|---|
| react, react-dom | 19.3.1 | MIT | Интерфейс, `src/main.tsx` |
| react-router | 8.5.2 | MIT | Маршруты (`src/App.tsx`) и плавные переходы между экранами (`viewTransition`) |
| lucide-react | 1.76.0 | ISC | Иконка «нет фото» (`src/components/DayPhoto.tsx`) |
| tailwindcss, @tailwindcss/vite | 4.3.5 | MIT | Базовые стили (`src/index.css`); основные стили страниц написаны на CSS |
| @fontsource/cormorant-garamond | 5.3.0 | OFL-1.1 (шрифт), MIT (пакет) | Заголовки и название на открытке. Шрифт лежит в сборке, к Google Fonts запросов нет |
| @fontsource/manrope | 5.3.0 | OFL-1.1 (шрифт), MIT (пакет) | Основной текст, дата и подпись открытки |
| motion | 14.14.0 | MIT | Есть в `package.json`, в `src/` не импортируется: вся анимация — CSS и Canvas |
| radix-ui | 1.8.1 | MIT | Есть в `package.json`, в `src/` не импортируется |

### Сборка и проверка

| Пакет | Версия | Лицензия | Назначение |
|---|---|---|---|
| vite | 8.3.8 | MIT | Dev-сервер и сборка |
| @vitejs/plugin-react | 6.3.0 | MIT | Плагин React для Vite |
| typescript | 6.0.3 | Apache-2.0 | Проверка типов (`tsc -b`) |
| eslint, typescript-eslint | 10.15.0, 8.73.0 | MIT | Линтер (`npm run lint`) |
| Playwright + Chromium (окружение разработки, не в репозитории) | — | Apache-2.0 | Проверка сценария в браузере, скриншоты и видео `docs/submission/media/` |
| ffmpeg (окружение разработки) | — | LGPL/GPL | Перекодирование видео демо в MP4 |

### Возможности браузера (без библиотек)

| API | Где | Зачем |
|---|---|---|
| Canvas 2D | `src/components/PostcardScene.tsx` | Растровый свет, погодная сцена, зерно |
| SVG | `src/components/Postcard.tsx` | Линия дня и метки плотности |
| View Transitions | `src/components/layout/Layout.tsx`, архив, создание дня | Переход открытки из архива в страницу дня |
| `speechSynthesis` | `src/components/SpeakButton.tsx` | Озвучка записи встроенным голосом браузера, по умолчанию выключена. Чужие голоса не используются |
| `prefers-reduced-motion` | CSS и `PostcardScene.tsx` | Без движения: тот же цвет и композиция, один статичный кадр |

### Внешние сервисы во фронтенде

- Запросы идут только к своему серверу (`/api`, `/media`).
- Плееры: встраиваемый Spotify (`open.spotify.com/embed`) и YouTube в режиме без cookie (`youtube-nocookie.com`). Загружаются, только если пользователь дал ссылку на песню. Файлы песен в репозитории не хранятся.

## Референсы и сторонний код

| Источник | Лицензия | Использование |
|---|---|---|
| arlan.me/vault | MIT (по брифу) | Не использован. Код не копировался |
| Magic UI | MIT | Не использован |
| Uiverse | MIT | Не использован |
| Aceternity UI | не проверялась | Не использован |
| bencho.dev | — | Только как источник идей, по брифу. Код не копировался |

Все эффекты (проявка, растровый свет, погода, дыхание линии, тени архива) написаны командой в этом репозитории. Код с сайтов без лицензии не копировался. Сайты из списка не открывались из среды разработки (нет выхода в интернет), поэтому лицензии в таблице указаны по брифу.

## ИИ-инструменты при разработке

Код и тексты частично написаны с помощью Claude Code (Anthropic). Это отражено в коммитах (строка `Co-Authored-By`). В работающем продукте ИИ не используется.
