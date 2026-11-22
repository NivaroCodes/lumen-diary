import { useEffect, useMemo, useState } from 'react'
import type { CSSProperties } from 'react'
import { Link, useParams } from 'react-router'
import Postcard from '../components/Postcard'
import type { WhyGroup } from '../components/Postcard'
import { formatLongDate } from '../components/postcard-model'
import { motionPlan } from '../components/postcard-motion'
import { errorMessage, getDay, musicEmbed, songTitle } from '../days-api'
import type { DayRecord, ExplainItem } from '../days-api'
import SpeakButton from '../components/SpeakButton'
import Letters from '../components/Letters'

const groups: { id: WhyGroup; label: string; lede: string }[] = [
  { id: 'color', label: 'Цвет и свет', lede: 'Палитра и свет взяты из фото и времени суток.' },
  { id: 'texture', label: 'Фактура', lede: 'Зерно, мягкость и штриховка погоды.' },
  { id: 'composition', label: 'Композиция', lede: 'Сколько элементов и куда идёт линия.' },
  { id: 'motion', label: 'Движение', lede: 'Ритм, размах и характер движения — из песни и погоды.' },
]

function groupOf(param: string): WhyGroup {
  if (param.startsWith('texture.')) return 'texture'
  if (param.startsWith('motion.') || param === 'line.amplitude' || param === 'line.roughness') return 'motion'
  if (param.startsWith('density.') || param.startsWith('line.')) return 'composition'
  return 'color'
}

const paramNames: Record<string, string> = {
  'light.direction_deg': 'Направление света', 'light.intensity': 'Яркость света', 'light.temperature_k': 'Температура света',
  'palette.colors': 'Палитра', 'palette.saturation': 'Насыщенность', contrast: 'Контраст',
  'density.value': 'Плотность', 'density.elements': 'Элементы', 'texture.weather': 'Погодная фактура',
  'texture.grain': 'Зерно', 'texture.blur': 'Мягкость фото', 'line.trajectory': 'Ход линии',
  'line.amplitude': 'Размах линии', 'line.roughness': 'Шероховатость линии', 'line.color_index': 'Цвет линии',
  'motion.reveal_ms': 'Длина проявки', 'motion.pulse_ms': 'Пульс', 'motion.character': 'Характер движения',
  'motion.scene': 'Фоновая сцена',
}

const valueNames: Record<string, string> = {
  smooth: 'плавный', sharp: 'резкий', neutral: 'нейтральный', rain: 'дождь', fog: 'туман', snow: 'снег',
  sun: 'солнце', cloud: 'облака', still: 'неподвижная', none: 'нет', rising: 'вверх', falling: 'вниз',
  wave: 'волна', flat: 'ровно',
}

function formatValue(item: ExplainItem) {
  const { value, param } = item
  if (Array.isArray(value)) return value.join(', ')
  if (typeof value === 'string') return valueNames[value] ?? value
  if (typeof value !== 'number') return ''
  if (param.endsWith('_ms')) return `${value} мс`
  if (param.endsWith('_deg')) return `${value}°`
  if (param.endsWith('_k')) return `${value} K`
  return String(value)
}

function provenanceLabel(item: ExplainItem) {
  if (item.provenance === 'unknown') return 'данных нет'
  if (item.provenance === 'entered') {
    return item.source?.startsWith('context.') ? 'выбрано вами' : 'оценено по описанию или выбрано'
  }
  if (item.source?.startsWith('photos.')) return 'измерено по фото'
  if (item.source?.startsWith('text.')) return 'найдено в тексте'
  return 'правило системы'
}

const weatherNames = { rain: 'дождь', fog: 'туман', cloud: 'облачно', sun: 'солнце' } as const
const modeNames = { major: 'мажор', minor: 'минор' } as const

export default function MemoryPage() {
  const { id } = useParams<'id'>()
  const [result, setResult] = useState<{ id: string; day?: DayRecord; error?: string }>()
  const [group, setGroup] = useState<WhyGroup>('color')
  const [pointing, setPointing] = useState(false)
  const [playing, setPlaying] = useState(true)
  const [revealKey, setRevealKey] = useState(0)

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
  const day = current?.day
  const plan = useMemo(() => (day ? motionPlan(day.visual) : null), [day])

  if (!current) {
    return (
      <div className="memory grid12">
        <h1 tabIndex={-1} className="page-title" aria-label="Открытка дня">Проявляем…</h1>
        <div className="memory-card"><div className="skeleton" /></div>
        <p role="status" className="status-line memory-side">Загружаем открытку.</p>
      </div>
    )
  }

  if (current.error || !day || !plan) {
    return (
      <div className="memory grid12">
        <div>
          <h1 tabIndex={-1} className="page-title">Открытка не открылась</h1>
          <p role="alert" className="error-line" style={{ marginTop: 16 }}>{current.error}</p>
          <p style={{ marginTop: 24 }}><Link to="/archive" className="btn" viewTransition>Открыть архив</Link></p>
        </div>
      </div>
    )
  }

  const { music, explain } = day
  const context = day.profile.context ?? {}
  const embed = musicEmbed(music.url)
  const items = explain.filter((item) => groupOf(item.param) === group)
  const mode = music.mode && music.mode !== 'unknown' ? music.mode : null

  return (
    <article aria-labelledby="memory-title" className="memory grid12">
      <div className="memory-card">
        <div style={{ viewTransitionName: `day-${day.id}` } as CSSProperties}>
          <Postcard
            key={revealKey}
            day={{ date: day.date, photos: day.photos, visual: day.visual, place: context.place }}
            playing={playing}
            highlight={pointing ? group : null}
          />
        </div>
      </div>

      <div className="memory-side">
        <header className="memory-head">
          <h1 id="memory-title" tabIndex={-1} className="page-title" aria-label={day.title}>
            <span key={revealKey} aria-hidden="true"><Letters text={day.title} stepMs={plan.letterStepMs} /></span>
          </h1>
          <dl className="memory-facts">
            <dt>Дата</dt><dd><time dateTime={day.date}>{formatLongDate(day.date)}</time></dd>
            {context.place && (<><dt>Место</dt><dd>{context.place}</dd></>)}
            <dt>Погода</dt>
            <dd>
              {context.weather ? `${weatherNames[context.weather]}, выбрано вами`
                : plan.scene !== 'still' ? `${valueNames[plan.scene]}, найдено в тексте` : 'не указана'}
            </dd>
            {day.folder && (<><dt>Папка дня</dt><dd className="folder">{day.folder}</dd></>)}
          </dl>
          <div className="memory-actions">
            <button type="button" className="btn" onClick={() => setRevealKey((key) => key + 1)}>Проявить заново</button>
            <button type="button" className="btn" aria-pressed={!playing} onClick={() => setPlaying((value) => !value)}>
              {playing ? 'Остановить движение' : 'Включить движение'}
            </button>
            <SpeakButton text={day.text} plan={plan} energy={music.energy ?? null} />
          </div>
        </header>

        <section aria-labelledby="music-title">
          <h2 id="music-title" className="section-title">Песня дня</h2>
          <p className="music-desc">{songTitle(music)}</p>
          <ul className="music-meta" aria-label="Что система знает о песне">
            {typeof music.tempo_bpm === 'number'
              ? <li>Темп {music.tempo_bpm} BPM</li>
              : <li data-unknown="true">Темп неизвестен</li>}
            {typeof music.energy === 'number'
              ? <li>Энергия {music.energy}</li>
              : <li data-unknown="true">Энергия неизвестна</li>}
            {mode ? <li>Лад: {modeNames[mode]}</li> : <li data-unknown="true">Лад неизвестен</li>}
            {music.genre && music.genre !== 'unknown' && <li>Жанр: {music.genre}</li>}
          </ul>
          {!mode && (
            <p className="why-note">Лад неизвестен, поэтому контраст задают только фото, а движение остаётся нейтральным.</p>
          )}
          {/* Spotify встраиваем. YouTube часто запрещает встраивание и показывает серую ошибку,
              поэтому вместо плеера даём карточку: название песни (выше) и кнопку «Открыть по ссылке». */}
          {embed?.kind === 'spotify' && (
            <iframe
              src={embed.src}
              title={embed.title}
              className="player"
              height={152}
              loading="lazy"
              allow="encrypted-media; clipboard-write; picture-in-picture"
              referrerPolicy="strict-origin-when-cross-origin"
            />
          )}
          {music.url && (
            <p style={{ margin: '12px 0 0' }}>
              <a href={music.url} target="_blank" rel="noopener noreferrer" className="text-link">
                Открыть песню по ссылке<span className="pc-sr"> (в новой вкладке)</span>
              </a>
            </p>
          )}
        </section>

        <section
          aria-labelledby="why-title"
          onPointerEnter={() => setPointing(true)}
          onPointerLeave={() => setPointing(false)}
          onFocus={() => setPointing(true)}
          onBlur={(event) => { if (!event.currentTarget.contains(event.relatedTarget)) setPointing(false) }}
        >
          <h2 id="why-title" className="section-title">Почему так</h2>
          <div className="why-tabs" role="group" aria-label="Что показать">
            {groups.map((item) => (
              <button key={item.id} type="button" className="btn" aria-pressed={group === item.id}
                aria-controls="why-list" onClick={() => setGroup(item.id)}>
                {item.label}
              </button>
            ))}
          </div>
          <p className="why-note" style={{ margin: '0 0 12px' }}>
            {groups.find((item) => item.id === group)?.lede} На открытке подсвечены слои, к которым это относится.
          </p>
          <ul id="why-list" className="why-list" aria-live="polite">
            {items.map((item) => (
              <li key={item.param} className="why-item">
                <p className="why-text">{item.text_ru}</p>
                <span className="why-rule">{item.rule}</span>
                <span className="why-meta">
                  <span>{paramNames[item.param] ?? item.param}: <b>{formatValue(item)}</b></span>
                  <span className="why-source" data-prov={item.provenance}>{provenanceLabel(item)}</span>
                </span>
              </li>
            ))}
          </ul>
          {group === 'motion' && (
            <>
              <h3 className="section-title" style={{ fontSize: 24, margin: '28px 0 8px' }}>Как это движется</h3>
              <ul className="why-list">
                {plan.notes.map((note) => (
                  <li key={note.rule} className="why-item">
                    <p className="why-text">{note.text}</p>
                    <span className="why-rule">{note.rule}</span>
                  </li>
                ))}
              </ul>
            </>
          )}
        </section>

        <p><Link to="/archive" className="text-link" viewTransition>Все дни в архиве</Link></p>
      </div>
    </article>
  )
}
