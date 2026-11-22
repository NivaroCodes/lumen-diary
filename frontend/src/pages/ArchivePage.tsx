import { useEffect, useState } from 'react'
import type { CSSProperties } from 'react'
import { Link } from 'react-router'
import DayPhoto from '../components/DayPhoto'
import Postcard from '../components/Postcard'
import { formatDayDate } from '../components/postcard-model'
import { lightGeometry } from '../components/postcard-visual'
import { errorMessage, listDays } from '../days-api'
import type { DaySummary } from '../days-api'

const monthNames = ['январь', 'февраль', 'март', 'апрель', 'май', 'июнь', 'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь']

function byMonth(days: DaySummary[]) {
  const groups = new Map<string, DaySummary[]>()
  for (const day of days) {
    const key = day.date.slice(0, 7)
    groups.set(key, [...(groups.get(key) ?? []), day])
  }
  return [...groups].map(([key, items]) => {
    const [year, month] = key.split('-').map(Number)
    return { key, label: `${monthNames[month - 1] ?? key} ${year}`, items }
  })
}

// Тень падает от источника света открытки (R-LIGHT-01), наклон при наведении — от seed.
function printStyle(day: DaySummary): CSSProperties {
  if (!day.visual) return {}
  const { x, y } = lightGeometry(day.visual)
  const dx = Math.round((0.5 - x) * 24)
  const dy = Math.round((0.5 - y) * 24) + 8
  const tilt = ((day.visual.seed % 7) - 3) * 0.35
  return {
    '--rest-shadow': `${dx / 3}px ${dy / 3}px 10px -6px rgb(36 32 27 / .35)`,
    '--lift-shadow': `${dx}px ${dy + 10}px 32px -12px rgb(36 32 27 / .5)`,
    '--tilt': `${tilt}deg`,
    viewTransitionName: `day-${day.id}`,
  } as CSSProperties
}

function ArchiveItem({ day }: { day: DaySummary }) {
  const [active, setActive] = useState(false)
  return (
    <Link
      to={`/memory/${encodeURIComponent(day.id)}`}
      viewTransition
      className="archive-item"
      onPointerEnter={() => setActive(true)}
      onPointerLeave={() => setActive(false)}
      onFocus={() => setActive(true)}
      onBlur={() => setActive(false)}
    >
      <div className="archive-print" style={printStyle(day)}>
        {day.visual ? (
          <Postcard day={{ date: day.date, photos: day.photos ?? [], visual: day.visual, place: day.place }}
            reveal={false} playing={active} compact />
        ) : (
          <div style={{ aspectRatio: '4 / 5' }}><DayPhoto src={day.preview_url} alt="" compact /></div>
        )}
      </div>
      <div className="archive-caption">
        <h3 className="archive-title">{day.title}</h3>
        <time dateTime={day.date} className="archive-date">{formatDayDate(day.date)}</time>
      </div>
      {day.folder && <p className="archive-folder">Папка: {day.folder}</p>}
    </Link>
  )
}

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
  const count = current?.days?.length ?? 0

  return (
    <div>
      <header className="archive-head">
        <h1 tabIndex={-1} className="page-title">Архив</h1>
        <p className="page-lede">
          {current?.days && count > 0
            ? `Сохранено дней: ${count}. Наведите на открытку, чтобы она ожила, и откройте её, чтобы узнать, почему она такая.`
            : 'Здесь собираются все открытки, новые сверху.'}
        </p>
      </header>

      {!current && (
        <>
          <p role="status" className="pc-sr">Загружаем архив.</p>
          <ul className="archive-wall grid12" aria-hidden="true">
            {[0, 1, 2].map((key) => <li key={key}><div className="skeleton" /></li>)}
          </ul>
        </>
      )}

      {current?.error && (
        <div role="alert" style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: 16 }}>
          <p className="error-line">{current.error}</p>
          <button type="button" className="btn" onClick={() => setAttempt((value) => value + 1)}>Загрузить снова</button>
        </div>
      )}

      {current?.days && count === 0 && (
        <section className="archive-empty" aria-labelledby="empty-title">
          <h2 id="empty-title">Пока ни одного дня</h2>
          <p>Опишите сегодняшний день, добавьте фото и песню — открытка появится здесь.</p>
          <Link to="/" className="btn btn-solid" viewTransition>Записать день</Link>
        </section>
      )}

      {current?.days && count > 0 && byMonth(current.days).map((month) => (
        <section key={month.key} className="archive-group" aria-labelledby={`month-${month.key}`}>
          <h2 id={`month-${month.key}`} className="archive-month">{month.label}</h2>
          <ul className="archive-wall grid12">
            {month.items.map((day) => <li key={day.id}><ArchiveItem day={day} /></li>)}
          </ul>
        </section>
      ))}
    </div>
  )
}
