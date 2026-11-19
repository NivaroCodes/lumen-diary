import { Link } from 'react-router'

export default function NotFoundPage() {
  return (
    <div className="space-y-4">
      <h1 tabIndex={-1} className="text-3xl font-bold sm:text-4xl">404 — Страница не найдена</h1>
      <Link
        to="/"
        className="inline-block rounded-sm text-(color:--color-accent) underline underline-offset-4 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-(--color-accent)"
      >
        Вернуться на главную
      </Link>
    </div>
  )
}
