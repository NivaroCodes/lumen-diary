import { useEffect, useState } from 'react'
import { Archive } from 'lucide-react'
import { Link } from 'react-router'
import DayPhoto from '../components/DayPhoto'
import { formatDayDate } from '../components/postcard-model'
import { errorMessage, listDays } from '../days-api'
import type { DaySummary } from '../days-api'

const focusOutline = 'focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-(--color-accent)'
const linkStyle = 'rounded-sm text-(color:--color-accent) underline underline-offset-4 ' + focusOutline

export default function ArchivePage() {
  const [attempt, setAttempt] = useState(0)
  const [result, setResult] = useState<{ attempt: number; days?: DaySummary[]; error?: string }>()

  useEffect(() => {
    let active = true
    listDays().then(
      (days) => { if (active) setResult({ attempt, days }) },
      (error: unknown) => { if (active) setResult({ attempt, error: errorMessage(error) }) },
    )
    return () => { active = false }
  }, [attempt])

  const current = result && result.attempt === attempt ? result : undefined

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 tabIndex={-1} className="text-3xl font-bold sm:text-4xl">Архив</h1>
        <p className="max-w-prose text-(color:--color-text-muted)">
          Все сохранённые дни, новые сверху. Выберите день, чтобы открыть открытку.
        </p>
      </div>

      {!current && (
        <p role="status" className="text-sm text-(color:--color-text-muted) animate-pulse">Загружаем архив…</p>
      )}

      {current?.error && (
        <div role="alert" className="flex flex-col items-start gap-3 rounded-(--radius-lg) border border-(--color-border) bg-(--color-surface) p-4">
          <p className="text-sm text-red-300">{current.error}</p>
          <button
            type="button"
            onClick={() => setAttempt((value) => value + 1)}
            className={'rounded-(--radius-sm) border border-(--color-border) px-3 py-2 text-sm font-semibold hover:bg-(--color-surface-hover) ' + focusOutline}
          >
            Повторить
          </button>
        </div>
      )}

      {current?.days && current.days.length === 0 && (
        <section aria-label="Коллекция открыток">
          <div className="flex flex-col items-center gap-3 rounded-(--radius-lg) border border-dashed border-(--color-border) bg-(--color-surface) px-4 py-8 text-center sm:py-12">
            <Archive aria-hidden="true" className="size-6 text-(color:--color-text-muted)" />
            <h2 className="text-lg font-semibold">Архив пока пуст</h2>
            <Link to="/" className={linkStyle}>
              Создать первый день
            </Link>
          </div>
        </section>
      )}

      {current?.days && current.days.length > 0 && (
        <section aria-label="Коллекция открыток" className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {current.days.map((day) => (
            <Link
              key={day.id}
              to={`/memory/${encodeURIComponent(day.id)}`}
              className={'flex flex-col overflow-hidden rounded-(--radius-lg) border border-(--color-border) bg-(--color-surface) hover:bg-(--color-surface-hover) ' + focusOutline}
            >
              <div className="aspect-[4/3] w-full">
                <DayPhoto src={day.preview_url} alt="" compact />
              </div>
              <div className="min-w-0 space-y-1 p-4">
                <h2 className="wrap-anywhere text-lg font-semibold">{day.title}</h2>
                <time dateTime={day.date} className="text-sm text-(color:--color-text-muted)">{formatDayDate(day.date)}</time>
              </div>
            </Link>
          ))}
        </section>
      )}
    </div>
  )
}
