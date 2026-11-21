# Инструменты и библиотеки

Список составлен по файлам репозитория: `backend/requirements.txt`, `backend/requirements-dev.txt`, `frontend/package.json` и импортам в `backend/app/` и `frontend/src/`. Версии Python-зависимостей совпадают с установленными в `backend/.venv` (проверено).

## Backend (Python 3.11)

### Рабочие зависимости (`backend/requirements.txt`)

| Пакет | Версия | Назначение в проекте |
|---|---|---|
| FastAPI | 0.165.0 | HTTP-сервер и маршруты: `app/main.py`, `app/routes_days.py` |
| uvicorn | 0.54.0 | ASGI-сервер для запуска: `uvicorn app.main:app` |
| Pydantic | 2.14.4 | Модели входа и ответа: `app/schemas.py` |
| python-multipart | 0.0.34 | Разбор `multipart/form-data` (форма `POST /api/days`), нужен FastAPI для `request.form()` |
| Pillow | 13.0.0 | Проверка и очистка фото: декодирование, удаление EXIF (`app/validation.py`, `app/photo_analysis.py`) |
| NumPy | 2.4.6 | Статистика по пикселям фото: яркость, контраст, тепло, доминирующие цвета (`app/photo_analysis.py`) |

### Для разработки и тестов (`backend/requirements-dev.txt`)

| Пакет | Версия | Назначение |
|---|---|---|
| pytest | 9.2.0 | Запуск тестов: `python -m pytest -q` в папке `backend/` |
| httpx | 0.28.1 | HTTP-клиент, на котором работает `fastapi.testclient` в `tests/conftest.py`. Также используется в примере из `backend/README.md` |

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
- **Анализ аудио не делается.** Музыкальные признаки (темп, энергия, лад) вводит пользователь, ссылка на песню не скачивается.

## Frontend (`frontend/package.json`)

### Зависимости времени выполнения (`dependencies`)

| Пакет | Версия в `package.json` | Назначение и использование |
|---|---|---|
| react | ^19.3.1 | Интерфейс, используется в `frontend/src` |
| react-dom | ^19.3.1 | Монтирование приложения (`src/main.tsx`) |
| react-router | ^8.5.2 | Маршрутизация страниц (архив, создание дня, память, 404) в `src/App.tsx` |
| lucide-react | ^1.76.0 | Иконки: `src/components/DayPhoto.tsx`, `src/pages/ArchivePage.tsx` |
| tailwindcss | ^4.3.5 | Стили: подключён через `@import "tailwindcss"` в `src/index.css` |
| @tailwindcss/vite | ^4.3.5 | Плагин Tailwind для Vite (`vite.config.ts`) |
| motion | ^14.14.0 | Анимации. В `package.json` есть, в `src/` пока не импортируется |
| radix-ui | ^1.8.1 | Примитивы интерфейса. В `package.json` есть, в `src/` пока не импортируется |

### Инструменты сборки и проверки (`devDependencies`)

| Пакет | Версия в `package.json` | Назначение |
|---|---|---|
| vite | ^8.3.6 | Dev-сервер и сборка (`npm run dev`, `npm run build`) |
| @vitejs/plugin-react | ^6.1.2 | Плагин React для Vite |
| typescript | ~6.0.3 | Проверка типов: `tsc -b` в `npm run build` |
| @types/react, @types/react-dom, @types/node | ^19.3.0, ^19.3.0, ^24.19.2 | Типы для React и Node |
| eslint | ^10.14.0 | Линтер (`npm run lint`) |
| @eslint/js, typescript-eslint, globals | ^10.0.1, ^8.72.1, ^17.13.0 | Конфигурация ESLint (`eslint.config.js`) |
| eslint-plugin-react-hooks, eslint-plugin-react-refresh | ^7.1.1, ^0.5.7 | Правила для React-хуков и HMR |

### Внешние сервисы во фронтенде

- В `frontend/src` пока нет вызовов `fetch` к backend и к внешним адресам (проверено поиском). Подключение к API — отдельная задача фронтенда.
