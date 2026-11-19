# Lumen Diary

Клиентская часть личного дневника команды Kernel для ArtTech Genesis Hackathon. На этапе FE-01 доступны экран «Новый день», демо-воспоминание и пустой архив.

## Технологический стек

- React, TypeScript и Vite.
- React Router для навигации.
- Tailwind CSS и CSS для стилей, Lucide React для иконок.
- Motion for React и Radix UI включены в стартовый стек для следующих этапов.
- ESLint для проверки кода.

## Требования к окружению

Node.js 24.x и npm 11.x.

## Локальный запуск

Из корня репозитория:

```sh
cd frontend
npm ci
npm run dev
```

## Проверка и сборка

В каталоге `frontend`:

```sh
npm run lint
npm run build
npm run preview
```

Vite сохраняет production-сборку в `dist/`. Команда `preview` запускает её локально.
