import { useEffect, useRef, useState } from 'react'
import type { CSSProperties, FormEvent } from 'react'
import { useNavigate } from 'react-router'
import { createDay, DayApiError, errorMessage, isMusicUrl, normalizeMusicUrl } from '../days-api'
import { inferMusicHints } from '../music-hints'
import type { Mode, Tempo } from '../music-hints'
import './create-day.css'

const formats = ['image/jpeg', 'image/png', 'image/webp']
const maxPhotos = 5
const maxPhotoSizeMb = 10
const genres = ['ambient', 'pop', 'rock', 'electronic', 'jazz', 'classical', 'hip-hop', 'folk', 'other', 'unknown']
const maxDayTextLength = 5000
const maxMusicUrlLength = 500
const maxMusicDescriptionLength = 300
const maxMusicMetadataLength = 200
const currentYear = new Date().getFullYear()
const musicTextFields = [
  { name: 'music_title', label: 'Название песни' },
  { name: 'music_artist', label: 'Исполнитель' },
]
const musicNumberFields = [
  { name: 'music_year', label: 'Год выпуска', min: 1900, max: currentYear, step: 1 },
]
const tempoOptions: { value: Tempo; label: string }[] = [
  { value: 'slow', label: 'Медленно' },
  { value: 'medium', label: 'Средне' },
  { value: 'fast', label: 'Быстро' },
]
const moodOptions: { value: Mode; label: string }[] = [
  { value: 'major', label: 'Светлое' },
  { value: 'minor', label: 'Тёмное' },
]
// Поля, которых нет в форме как отдельных элементов: их ошибки показываем в разделе «Уточнить».
const refineFields = ['music_tempo_bpm', 'music_energy', 'music_mode']
type Weather = 'rain' | 'fog' | 'cloud' | 'sun'
// Погода выбирается вручную, без внешних API. Без выбора погода берётся из текста записи.
const weatherOptions: { value: Weather; label: string }[] = [
  { value: 'rain', label: 'Дождь' },
  { value: 'fog', label: 'Туман' },
  { value: 'cloud', label: 'Облачно' },
  { value: 'sun', label: 'Солнце' },
]
const maxPlaceLength = 80
const dayFormFields = [
  'text', 'date', 'place', 'music_url', 'music_description', 'music_genre',
  ...musicTextFields.map(({ name }) => name),
  ...musicNumberFields.map(({ name }) => name),
]
// Значения по умолчанию только для отображения (подсветка чипов и карточка), в отправку не уходят.
const defaultTempo: Tempo = 'medium'
const defaultMood: Mode = 'minor'
// Положение капель в картинке «Атмосфера дня» (в координатах viewBox 320×224).
const dropX = [36, 84, 124, 196, 236, 284]

type SelectedPhoto = { id: number; file: File }

function trimField(value: string) {
  // eslint-disable-next-line no-control-regex -- Python also strips U+001C through U+001F.
  return value.replace(/^[\p{White_Space}\u001c-\u001f]+|[\p{White_Space}\u001c-\u001f]+$/gu, '')
}

function normalizeTextarea(value: string) {
  // Match the line endings sent by multipart/form-data.
  return trimField(value).replace(/\r\n?|\n/g, '\r\n')
}

function validateDayText(text: string) {
  if (!text) return 'Расскажите, как прошёл день.'
  // String iteration counts Unicode code points, matching Python's len().
  if ([...text].length > maxDayTextLength) return `Сократите запись до ${maxDayTextLength} символов.`
  return ''
}

function validatePhotos(files: File[]) {
  if (!files.length) return 'Добавьте хотя бы одно фото.'
  if (files.length > maxPhotos) {
    return `Можно добавить не больше ${maxPhotos} фото. Выберите меньше файлов или удалите фото из списка.`
  }
  for (const file of files) {
    if (file.size > maxPhotoSizeMb * 1024 * 1024) return `«${file.name}» — размер больше ${maxPhotoSizeMb} МБ.`
    if (!formats.includes(file.type)) return `«${file.name}» — выберите JPEG, PNG или WebP.`
    if (!file.size) return `«${file.name}» — файл пустой.`
  }
  return ''
}

function validateMusic(form: HTMLFormElement, data: FormData, choices: { tempo?: Tempo; mode?: Mode }) {
  const errors: Record<string, string> = {}
  const url = trimField(String(data.get('music_url') ?? ''))
  const description = normalizeTextarea(String(data.get('music_description') ?? ''))
  data.set('music_url', url)
  data.set('music_description', description)

  if (!url) errors.music_url = 'Добавьте ссылку на песню.'
  else if ([...url].length > maxMusicUrlLength) errors.music_url = `Ссылка должна быть не длиннее ${maxMusicUrlLength} символов.`
  // eslint-disable-next-line no-control-regex -- These characters also count as whitespace in Python.
  else if (/[\p{White_Space}\u001c-\u001f]/u.test(url)) errors.music_url = 'Уберите пробелы из ссылки.'
  else if (!/^https?:\/\/[^/?#\\]/i.test(url) || !isMusicUrl(url)) {
    errors.music_url = 'Укажите адрес песни, который начинается с https:// или http://.'
  }
  else data.set('music_url', normalizeMusicUrl(url))

  if (!description) errors.music_description = 'Коротко опишите песню.'
  else if ([...description].length > maxMusicDescriptionLength) {
    errors.music_description = `Сократите описание до ${maxMusicDescriptionLength} символов.`
  }

  for (const { name, label } of musicTextFields) {
    const value = trimField(String(data.get(name) ?? ''))
    if ([...value].length > maxMusicMetadataLength) {
      errors[name] = `${label} — до ${maxMusicMetadataLength} символов.`
    }
    if (value) data.set(name, value)
    else data.delete(name)
  }

  for (const { name, min, max, step } of musicNumberFields) {
    const input = form.elements.namedItem(name)
    if (!(input instanceof HTMLInputElement)) continue

    const { badInput, stepMismatch, rangeUnderflow, rangeOverflow } = input.validity
    if (badInput || stepMismatch) {
      errors[name] = step === 1 ? 'Укажите год целым числом.' : 'Введите число.'
    } else if (rangeUnderflow || rangeOverflow) {
      errors[name] = `Укажите значение от ${min} до ${max}.`
    } else if (input.value) {
      data.set(name, String(input.valueAsNumber))
    } else {
      data.delete(name)
    }
  }

  if (!data.get('music_genre')) data.delete('music_genre')

  // Темп, энергия и лад: явный выбор, иначе оценка по фразе. Отправляем только заданное.
  const { tempo_bpm, energy, mode, genre } = inferMusicHints(description, {
    ...choices,
    genre: String(data.get('music_genre') ?? '') || undefined,
  })
  if (tempo_bpm !== undefined) data.set('music_tempo_bpm', String(tempo_bpm))
  if (energy !== undefined) data.set('music_energy', String(energy))
  if (mode) data.set('music_mode', mode)
  if (genre) data.set('music_genre', genre)
  return errors
}

function PhotoPreview({ file, onRemove }: { file: File; onRemove: () => void }) {
  const image = useRef<HTMLImageElement>(null)
  const [previewFailed, setPreviewFailed] = useState(false)
  useEffect(() => {
    const url = URL.createObjectURL(file)
    image.current?.setAttribute('src', url)
    return () => URL.revokeObjectURL(url)
  }, [file])
  return (
    <li className="lm-photo-item">
      {previewFailed ? (
        <span className="lm-thumb lm-thumb-fallback">Нет превью</span>
      ) : (
        <img ref={image} alt="" onError={() => setPreviewFailed(true)} className="lm-thumb" />
      )}
      <span className="lm-photo-name">{file.name}</span>
      <button type="button" className="lm-link-button" onClick={onRemove} aria-label={`Удалить ${file.name}`}>
        Удалить
      </button>
    </li>
  )
}

export default function CreateDayPage() {
  const navigate = useNavigate()
  const [photos, setPhotos] = useState<SelectedPhoto[]>([])
  const nextPhotoId = useRef(0)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [pending, setPending] = useState(false)
  // undefined = пользователь ничего не выбрал: в отправку ничего не уходит, темп и лад берутся из описания.
  const [tempo, setTempo] = useState<Tempo>()
  const [mood, setMood] = useState<Mode>()
  const [weather, setWeather] = useState<Weather>()
  const submitting = useRef(false)
  const errorFocus = useRef<string | null>(null)
  // Только отображение: карточка и подсветка чипов показывают умолчания, но в отправку они не попадают.
  const tempoValue: Tempo = tempo ?? defaultTempo
  const moodValue: Mode = mood ?? defaultMood

  useEffect(() => {
    if (pending || !errorFocus.current) return
    const target = document.getElementById(errorFocus.current)
    errorFocus.current = null
    target?.closest('details')?.setAttribute('open', '')
    target?.focus()
  }, [errors, pending])

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (submitting.current) return
    const form = event.currentTarget
    const values = new FormData(form)
    const data = new FormData()
    for (const name of dayFormFields) {
      const value = values.get(name)
      if (typeof value === 'string' && value) data.set(name, value)
    }
    const fieldErrors: Record<string, string> = {}
    const text = normalizeTextarea(String(data.get('text') ?? ''))
    data.set('text', text)
    const textError = validateDayText(text)
    if (textError) fieldErrors.text = textError
    const photoError = validatePhotos(photos.map(({ file }) => file))
    if (photoError) fieldErrors.photos = photoError
    Object.assign(fieldErrors, validateMusic(form, data, { tempo, mode: mood }))
    const place = trimField(String(data.get('place') ?? '')).replace(/\s+/g, ' ')
    if ([...place].length > maxPlaceLength) fieldErrors.place = `Сократите место до ${maxPlaceLength} символов.`
    if (place) data.set('place', place)
    else data.delete('place')
    if (weather) data.set('weather', weather)
    setErrors(fieldErrors)
    const firstError = Object.keys(fieldErrors)[0]
    if (firstError) {
      const input = document.getElementById(firstError)
      input?.closest('details')?.setAttribute('open', '')
      input?.focus()
      return
    }

    for (const { file } of photos) data.append('photos', file)
    submitting.current = true
    setPending(true)
    try {
      const day = await createDay(data)
      navigate(`/memory/${encodeURIComponent(day.id)}`, { viewTransition: true })
    } catch (error) {
      const name = error instanceof DayApiError ? error.field : undefined
      const control = name ? form.elements.namedItem(name) : null
      const key = name && (refineFields.includes(name) || (control instanceof HTMLElement && control.id === name)) ? name : 'form'
      errorFocus.current = key === 'form' ? 'form-error' : refineFields.includes(key) ? 'music-refine' : key
      setErrors({ [key]: errorMessage(error) })
      submitting.current = false
      setPending(false)
    }
  }

  function field(name: string, className = 'lm-field') {
    return { id: name, name, className, 'aria-invalid': Boolean(errors[name]), 'aria-describedby': `${name}-error` }
  }

  function musicField(name: string, className = 'lm-field') {
    return {
      ...field(name, className),
      onChange: () => {
        if (errors[name]) setErrors((previous) => ({ ...previous, [name]: '' }))
      },
    }
  }

  function feedback(name: string) {
    return <p id={`${name}-error`} aria-live="polite" className="lm-error">{errors[name]}</p>
  }

  return (
    <div className="lm-create">
      <form onSubmit={submit} noValidate aria-busy={pending} className="lm-form">
        <fieldset disabled={pending} className="lm-fieldset">
          <header className="lm-head">
            <h1 tabIndex={-1} aria-label="Новый день" className="lm-title">
              {'Новый день'.split('').map((letter, index) => (
                <span key={index} aria-hidden="true" className="lm-letter" style={{ '--i': index } as CSSProperties}>
                  {letter === ' ' ? ' ' : letter}
                </span>
              ))}
            </h1>
            <p className="lm-lede">Опишите день, добавьте фото и песню. Из этого соберётся открытка.</p>
          </header>
          <div className="lm-grid">
            <div className="lm-col">
              <section className="lm-block">
                <label htmlFor="text" className="lm-label">Как прошёл день?</label>
                <p id="text-hint" className="lm-hint">
                  Обязательное поле. До {maxDayTextLength} символов.
                </p>
                <textarea
                  {...field('text', 'lm-field lm-textarea')}
                  required
                  rows={6}
                  aria-describedby="text-hint text-error"
                  onChange={(event) => {
                    if (!errors.text) return
                    const message = validateDayText(normalizeTextarea(event.currentTarget.value))
                    if (message !== errors.text) {
                      setErrors((previous) => ({ ...previous, text: message }))
                    }
                  }}
                />
                {feedback('text')}
                <div className="lm-date">
                  <label htmlFor="date" className="lm-small">Дата (необязательно)</label>
                  <input {...field('date')} type="date" />
                  {feedback('date')}
                </div>
              </section>

              <section className="lm-block" aria-labelledby="photos-heading">
                <h2 id="photos-heading" className="lm-label">Фотографии</h2>
                <p id="photos-hint" className="lm-hint">1–{maxPhotos} фото JPEG, PNG или WebP, до {maxPhotoSizeMb} МБ каждое.</p>
                <div className="lm-photo-actions">
                  <input
                    {...field('photos', 'lm-sr-only lm-file')}
                    type="file"
                    multiple
                    accept={formats.join(',')}
                    aria-describedby="photos-hint photos-error"
                    onChange={(event) => {
                      const selected = Array.from(event.currentTarget.files ?? [])
                      event.currentTarget.value = ''
                      if (!selected.length) return
                      const message = validatePhotos([...photos.map(({ file }) => file), ...selected])
                      setErrors((previous) => ({ ...previous, photos: message }))
                      if (message) return
                      const additions = selected.map((file) => ({ id: nextPhotoId.current++, file }))
                      setPhotos((previous) => [...previous, ...additions])
                    }}
                  />
                  <label htmlFor="photos" className="lm-pill">Выбрать</label>
                  <span role="status" className="lm-hint">Выбрано {photos.length} из {maxPhotos}</span>
                </div>
                {feedback('photos')}
                {photos.length > 0 && (
                  <ul className="lm-photo-list">
                    {photos.map(({ id, file }) => (
                      <PhotoPreview key={id} file={file} onRemove={() => {
                        setPhotos((previous) => previous.filter((photo) => photo.id !== id))
                        setErrors((previous) => ({ ...previous, photos: '' }))
                      }} />
                    ))}
                  </ul>
                )}
              </section>
            </div>

            <div className="lm-col">
              <section aria-labelledby="atmo-title" className="lm-block">
                <h2 id="atmo-title" className="lm-label">Атмосфера дня</h2>
                <div className="lm-atmo" data-tempo={tempoValue} data-mood={moodValue} data-weather={weather ?? 'text'}>
                  <svg className="lm-atmo-svg" viewBox="0 0 320 224" aria-hidden="true" focusable="false" preserveAspectRatio="xMidYMid slice">
                    {dropX.map((x, index) => (
                      <line key={x} x1={x} x2={x} y1={0} y2={14} className="lm-drop" style={{ '--i': index } as CSSProperties} />
                    ))}
                    <circle cx={248} cy={56} r={22} className="lm-sun" />
                    <g className="lm-fog">
                      {[60, 92, 124].map((y, index) => (
                        <line key={y} x1={20 + index * 18} x2={300 - index * 24} y1={y} y2={y} style={{ '--i': index } as CSSProperties} />
                      ))}
                    </g>
                    <path d="M196 70 a18 18 0 0 1 34 -8 a14 14 0 0 1 24 10 a12 12 0 0 1 -4 24 h-50 a14 14 0 0 1 -4 -26 z" className="lm-cloud" />
                    <g className="lm-bud">
                      <line x1={160} y1={136} x2={160} y2={200} className="lm-bud-line" />
                      <path d="M160 136 C 146 120, 142 98, 160 74 C 178 98, 174 120, 160 136 Z" className="lm-bud-line lm-petals" />
                      <path d="M160 136 C 150 134, 142 142, 140 152 M160 136 C 170 134, 178 142, 180 152" className="lm-bud-line" />
                    </g>
                  </svg>
                  <p className="lm-atmo-caption">
                    {weather ? weatherOptions.find((option) => option.value === weather)?.label : 'Погода по тексту записи'}
                  </p>
                </div>
                <div className="lm-line-field" role="group" aria-labelledby="weather-label">
                  <span id="weather-label" className="lm-small">Погода (необязательно)</span>
                  <p className="lm-hint">Выбор важнее слов в тексте: он задаёт фоновую сцену и фактуру открытки.</p>
                  <div className="lm-chips">
                    {weatherOptions.map(({ value, label }) => (
                      <button key={value} type="button" aria-pressed={weather === value} className="lm-chip"
                        onClick={() => setWeather(weather === value ? undefined : value)}>
                        {label}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="lm-line-field">
                  <label htmlFor="place" className="lm-small">Где это было (необязательно)</label>
                  <div className="lm-line-wrap">
                    <input {...field('place', 'lm-line-input')} type="text" maxLength={120} autoComplete="off" placeholder="Например: парк у дома" />
                    <span className="lm-line" aria-hidden="true" />
                  </div>
                  {feedback('place')}
                </div>
              </section>

              <section aria-labelledby="music-heading" className="lm-block">
                <h2 id="music-heading" className="lm-label">Музыка</h2>
                <label htmlFor="music_url" className="lm-small">Ссылка на песню</label>
                <input {...musicField('music_url')} type="url" required placeholder="https://…" />
                {feedback('music_url')}
                <label htmlFor="music_description" className="lm-small">Как звучит песня</label>
                <p id="music-description-hint" className="lm-hint">Например: медленная, тихая, с пианино. До {maxMusicDescriptionLength} символов.</p>
                <p className="lm-hint">Система оценит темп и настроение по этой фразе. Вы можете уточнить это ниже.</p>
                <textarea
                  {...musicField('music_description', 'lm-field lm-textarea')}
                  required
                  rows={3}
                  aria-describedby="music-description-hint music_description-error"
                />
                {feedback('music_description')}
                <details open className="lm-refine">
                  <summary id="music-refine" tabIndex={-1} className="lm-summary">Уточнить, если хотите</summary>
                  <div className="lm-refine-grid">
                    {musicTextFields.map(({ name, label }) => (
                      <div key={name} className="lm-line-field">
                        <label htmlFor={name} className="lm-small">{label}</label>
                        <div className="lm-line-wrap">
                          <input {...musicField(name, 'lm-line-input')} type="text" />
                          <span className="lm-line" aria-hidden="true" />
                        </div>
                        {feedback(name)}
                      </div>
                    ))}
                    {musicNumberFields.map(({ name, label, min, max, step }) => (
                      <div key={name} className="lm-line-field">
                        <label htmlFor={name} className="lm-small">{label}, {min}–{max}</label>
                        <div className="lm-line-wrap">
                          <input {...musicField(name, 'lm-line-input')} type="number" min={min} max={max} step={step} />
                          <span className="lm-line" aria-hidden="true" />
                        </div>
                        {feedback(name)}
                      </div>
                    ))}
                    <div className="lm-line-field">
                      <label htmlFor="music_genre" className="lm-small">Жанр</label>
                      <select {...musicField('music_genre')}>
                        <option value="">Не указан</option>
                        {genres.map((genre) => <option key={genre}>{genre}</option>)}
                      </select>
                      {feedback('music_genre')}
                    </div>
                    <div className="lm-line-field" role="group" aria-labelledby="music-tempo-label">
                      <span id="music-tempo-label" className="lm-small">Темп</span>
                      <div className="lm-chips">
                        {tempoOptions.map(({ value, label }) => (
                          <button key={value} type="button" aria-pressed={tempoValue === value} className="lm-chip"
                            onClick={() => { setTempo(tempo === value ? undefined : value); setErrors((p) => ({ ...p, music_tempo_bpm: '', music_energy: '' })) }}>
                            {label}
                          </button>
                        ))}
                      </div>
                      {feedback('music_tempo_bpm')}
                      {feedback('music_energy')}
                    </div>
                    <div className="lm-line-field" role="group" aria-labelledby="music-mood-label">
                      <span id="music-mood-label" className="lm-small">Настроение</span>
                      <div className="lm-chips">
                        {moodOptions.map(({ value, label }) => (
                          <button key={value} type="button" aria-pressed={moodValue === value} className="lm-chip"
                            onClick={() => { setMood(mood === value ? undefined : value); setErrors((p) => ({ ...p, music_mode: '' })) }}>
                            {label}
                          </button>
                        ))}
                      </div>
                      {feedback('music_mode')}
                    </div>
                  </div>
                </details>
              </section>

              <p id="form-error" role="alert" tabIndex={-1} className="lm-error">{errors.form}</p>
              <button type="submit" className="lm-primary">
                {pending ? 'Проявляем открытку…' : errors.form ? 'Повторить отправку' : 'Создать открытку'}
              </button>
            </div>
          </div>
        </fieldset>
      </form>
      <p role="status" className="lm-sr-only">{pending ? 'Проявляем открытку…' : ''}</p>
    </div>
  )
}
