import { Archive } from 'lucide-react'
import { Link } from 'react-router'

export default function ArchivePage() {
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 tabIndex={-1} className="text-3xl font-bold sm:text-4xl">Архив</h1>
        <p className="max-w-prose text-(color:--color-text-muted)">
          Здесь будут храниться открытки. Из архива можно будет открыть любое сохранённое воспоминание.
        </p>
      </div>

      <section aria-label="Коллекция открыток" className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div className="col-span-full flex flex-col items-center gap-3 rounded-(--radius-lg) border border-dashed border-(--color-border) bg-(--color-surface) px-4 py-8 text-center sm:py-12">
          <Archive aria-hidden="true" className="size-6 text-(color:--color-text-muted)" />
          <h2 className="text-lg font-semibold">Архив пока пуст</h2>
          <Link
            to="/"
            className="rounded-sm text-(color:--color-accent) underline underline-offset-4 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-(--color-accent)"
          >
            Создать первый день
          </Link>
        </div>
      </section>
    </div>
  )
}
