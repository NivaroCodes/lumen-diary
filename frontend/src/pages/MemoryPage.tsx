import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router'
import Postcard from '../components/Postcard'
import { formatDayDate } from '../components/postcard-model'
import { getDay, errorMessage } from '../days-api'
import type { DayRecord } from '../days-api'

const panel = 'space-y-2 rounded-(--radius-md) border border-(--color-border) bg-(--color-surface) p-4'
const mutedText = 'text-sm text-(color:--color-text-muted)'
const linkStyle = 'rounded-sm text-(color:--color-accent) underline underline-offset-4 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-(--color-accent)'

// Ссылка на трек Spotify превращается в embed; для других ссылок embed не показываем.
function spotifyEmbedUrl(url: string | undefined) {
  try {
    const parsed = new URL(url ?? '')
    if (parsed.hostname !== 'open.spotify.com' && parsed.hostname !== 'www.open.spotify.com') return null
    const match = /^(?:\/intl-[a-z]{2})?\/track\/([A-Za-z0-9]+)\/?$/.exec(parsed.pathname)
    return match ? `https://open.spotify.com/embed/track/${match[1]}` : null
  } catch {
    return null
  }
}

function explainValue(value: unknown) {
  return typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean' ? String(value) : null
}

export default function MemoryPage() {
  const { id } = useParams<'id'>()
  const [result, setResult] = useState<{ id: string; day?: DayRecord; error?: string }>()

  useEffect(() => {
    if (!id) return
    let active = true
    getDay(id).then(
      (day) => { if (active) setResult({ id, day }) },
      (error: unknown) => { if (active) setResult({ id, error: errorMessage(error) }) },
    )
    return () => { active = false }
  }, [id])

  const current = result && result.id === id ? result : undefined

  if (!current) {
    return (
      <div className="space-y-4">
        <h1 tabIndex={-1} className="text-3xl font-bold sm:text-4xl">Воспоминание дня</h1>
        <p role="status" className={mutedText + ' animate-pulse'}>Загружаем открытку…</p>
      </div>
    )
  }

  if (current.error || !current.day) {
    return (
      <div className="space-y-4">
        <h1 tabIndex={-1} className="text-3xl font-bold sm:text-4xl">Не удалось открыть воспоминание</h1>
        <p role="alert" className="text-sm text-red-300">{current.error}</p>
        <Link to="/archive" className={linkStyle}>В архив</Link>
      </div>
    )
  }

  const day = current.day
  const { music, explain } = day
  const embedUrl = spotifyEmbedUrl(music.url)

  return (
    <article aria-labelledby="memory-title" className="space-y-6">
      <div className="space-y-2">
        <h1 id="memory-title" tabIndex={-1} className="text-3xl font-bold sm:text-4xl">{day.title}</h1>
        <dl className="text-sm text-(color:--color-text-muted)">
          <div className="flex flex-wrap gap-x-2">
            <dt className="font-medium">Дата записи</dt>
            <dd><time dateTime={day.date}>{formatDayDate(day.date)}</time></dd>
          </div>
          <div className="flex flex-wrap gap-x-2">
            <dt className="font-medium">ID записи</dt>
            <dd className="min-w-0 break-all">{day.id}</dd>
          </div>
        </dl>
      </div>

      <div className="grid items-start gap-6 md:grid-cols-[minmax(0,22rem)_minmax(0,1fr)]">
        <div className="w-full max-w-[22rem] justify-self-center md:justify-self-start">
          <Postcard day={{ date: day.date, photos: day.photos, visual: day.visual }} />
        </div>

        <div className="min-w-0 space-y-4">
          <section aria-labelledby="memory-music-title" className={panel}>
            <h2 id="memory-music-title" className="text-lg font-semibold">Музыка</h2>
            {music.description && <p className="text-sm">{music.description}</p>}
            <dl className={mutedText + ' space-y-1'}>
              <div className="flex flex-wrap gap-x-2">
                <dt className="font-medium">Жанр</dt>
                <dd>{music.genre || 'не указан'}</dd>
              </div>
              {typeof music.tempo_bpm === 'number' && (
                <div className="flex flex-wrap gap-x-2">
                  <dt className="font-medium">Темп</dt>
                  <dd>{music.tempo_bpm} BPM</dd>
                </div>
              )}
            </dl>
            {music.url && (
              <a
                href={music.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-block rounded-(--radius-sm) border border-(--color-border) px-3 py-2 text-sm font-semibold hover:bg-(--color-surface-hover) focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-(--color-accent)"
              >
                Открыть в Spotify
              </a>
            )}
            {embedUrl && (
              <iframe
                src={embedUrl}
                title="Проигрыватель Spotify"
                width="100%"
                height="152"
                loading="lazy"
                allow="encrypted-media; clipboard-write"
                className="rounded-(--radius-sm)"
              />
            )}
          </section>

          <section aria-labelledby="memory-explanation-title" className={panel}>
            <h2 id="memory-explanation-title" className="text-lg font-semibold">Почему так</h2>
            {explain.length === 0 ? (
              <p className={mutedText}>Объяснение недоступно</p>
            ) : (
              <ul className="space-y-3">
                {explain.map((item, index) => {
                  const value = explainValue(item.value)
                  return (
                    <li key={`${item.param}-${index}`} className="space-y-1 text-sm">
                      <code className="break-all text-(color:--color-accent)">
                        {item.param}{value !== null ? ` = ${value}` : ''}
                      </code>
                      <p className={mutedText}>{item.text_ru}</p>
                    </li>
                  )
                })}
              </ul>
            )}
          </section>
        </div>
      </div>

      <Link to="/" className={linkStyle + ' inline-block'}>
        Вернуться к созданию дня
      </Link>
    </article>
  )
}
