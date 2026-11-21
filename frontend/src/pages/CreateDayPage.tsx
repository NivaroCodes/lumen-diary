import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate } from 'react-router'
import { createDay, DayApiError, errorMessage, isMusicUrl } from '../days-api'

const panel = 'min-w-0 space-y-3 rounded-(--radius-md) border border-(--color-border) bg-(--color-surface) p-4 sm:p-5'
const fieldStyle = 'w-full rounded-(--radius-sm) border border-(--color-border) bg-(--color-background) px-3 py-2 aria-invalid:border-red-400'
const mutedText = 'text-sm text-(color:--color-text-muted)'
const focusOutline = 'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-(--color-accent)'
const errorStyle = 'wrap-anywhere text-sm text-red-300'
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
  { name: 'music_tempo_bpm', label: 'Темп (BPM)', min: 40, max: 220, step: 'any' },
  { name: 'music_energy', label: 'Энергия', min: 0, max: 1, step: 'any' },
]
const dayFormFields = [
  'text', 'date', 'music_url', 'music_description', 'music_genre', 'music_mode',
  ...musicTextFields.map(({ name }) => name),
  ...musicNumberFields.map(({ name }) => name),
]

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

function validateMusic(form: HTMLFormElement, data: FormData) {
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

  for (const name of ['music_genre', 'music_mode']) {
    if (!data.get(name)) data.delete(name)
  }
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
    <li className="flex items-start gap-3 sm:items-center">
      {previewFailed ? (
        <span className="grid size-16 shrink-0 place-items-center rounded bg-(--color-background) px-1 text-center text-xs">Нет превью</span>
      ) : (
        <img ref={image} alt="" onError={() => setPreviewFailed(true)} className="size-16 shrink-0 rounded object-cover" />
      )}
      <div className="min-w-0 flex-1 sm:flex sm:items-center sm:gap-3">
        <span className="block min-w-0 wrap-anywhere text-sm sm:flex-1">{file.name}</span>
        <button
          type="button"
          className={'shrink-0 rounded py-2 text-sm underline sm:px-2 ' + focusOutline}
          onClick={onRemove}
          aria-label={`Удалить ${file.name}`}
        >
          Удалить
        </button>
      </div>
    </li>
  )
}

export default function CreateDayPage() {
  const navigate = useNavigate()
  const [photos, setPhotos] = useState<SelectedPhoto[]>([])
  const nextPhotoId = useRef(0)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [pending, setPending] = useState(false)
  const submitting = useRef(false)
  const errorFocus = useRef<string | null>(null)

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
    Object.assign(fieldErrors, validateMusic(form, data))
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
      navigate(`/memory/${encodeURIComponent(day.id)}`)
    } catch (error) {
      const name = error instanceof DayApiError ? error.field : undefined
      const control = name ? form.elements.namedItem(name) : null
      const key = name && control instanceof HTMLElement && control.id === name ? name : 'form'
      errorFocus.current = key === 'form' ? 'form-error' : key
      setErrors({ [key]: errorMessage(error) })
      submitting.current = false
      setPending(false)
    }
  }

  function field(name: string) {
    return { id: name, name, className: fieldStyle, 'aria-invalid': Boolean(errors[name]), 'aria-describedby': `${name}-error` }
  }

  function musicField(name: string) {
    return {
      ...field(name),
      className: fieldStyle + ' ' + focusOutline,
      onChange: () => {
        if (errors[name]) setErrors((previous) => ({ ...previous, [name]: '' }))
      },
    }
  }

  function feedback(name: string) {
    return <p id={`${name}-error`} aria-live="polite" className={errorStyle}>{errors[name]}</p>
  }

  return (
    <div className="space-y-6">
      <h1 tabIndex={-1} className="text-3xl font-bold sm:text-4xl">Новый день</h1>
      <form onSubmit={submit} noValidate aria-busy={pending}>
        <fieldset disabled={pending} className="space-y-4">
          <section className={panel}>
            <label htmlFor="text" className="block text-lg font-semibold">Как прошёл день?</label>
            <p id="text-hint" className="text-sm text-(color:--color-text-muted)">
              Обязательное поле. До {maxDayTextLength} символов.
            </p>
            <textarea
              {...field('text')}
              required
              rows={6}
              className={fieldStyle + ' resize-y text-base focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-(--color-accent)'}
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
            <div className="max-w-56">
              <label htmlFor="date" className="block text-sm">Дата (необязательно)</label>
              <input {...field('date')} type="date" />
              {feedback('date')}
            </div>
          </section>
          <section className={panel} aria-labelledby="photos-heading">
            <h2 id="photos-heading" className="text-lg font-semibold">Фотографии</h2>
            <p id="photos-hint" className={mutedText}>1–{maxPhotos} фото JPEG, PNG или WebP, до {maxPhotoSizeMb} МБ каждое.</p>
            <div className="flex flex-wrap items-center gap-3">
              <input
                {...field('photos')}
                type="file"
                multiple
                accept={formats.join(',')}
                className="peer sr-only"
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
              <label htmlFor="photos" className="cursor-pointer rounded border border-(--color-border) bg-(--color-background) px-3 py-2 text-sm font-semibold hover:bg-(--color-surface-hover) peer-aria-invalid:border-red-400 peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-(--color-accent)">
                Выбрать фотографии
              </label>
              <span role="status" className={mutedText}>Выбрано {photos.length} из {maxPhotos}</span>
            </div>
            {feedback('photos')}
            {photos.length > 0 && (
              <ul className="space-y-2">
                {photos.map(({ id, file }) => (
                  <PhotoPreview key={id} file={file} onRemove={() => {
                    setPhotos((previous) => previous.filter((photo) => photo.id !== id))
                    setErrors((previous) => ({ ...previous, photos: '' }))
                  }} />
                ))}
              </ul>
            )}
          </section>
          <section className={panel} aria-labelledby="music-heading">
            <h2 id="music-heading" className="text-lg font-semibold">Музыка</h2>
            <label htmlFor="music_url" className="block text-sm">Ссылка на песню</label>
            <input {...musicField('music_url')} type="url" required placeholder="https://…" />
            {feedback('music_url')}
            <label htmlFor="music_description" className="block text-sm">Описание песни</label>
            <p id="music-description-hint" className={mutedText}>Опишите темп, настроение или жанр. До {maxMusicDescriptionLength} символов.</p>
            <textarea {...musicField('music_description')} required rows={3}
              className={fieldStyle + ' resize-y text-base ' + focusOutline} aria-describedby="music-description-hint music_description-error" />
            {feedback('music_description')}
            <details>
              <summary className={'cursor-pointer rounded text-sm underline ' + focusOutline}>Добавить сведения о песне</summary>
              <div className="mt-3 grid gap-3 sm:grid-cols-2">
                {musicTextFields.map(({ name, label }) => (
                  <div key={name} className="min-w-0 space-y-1">
                    <label htmlFor={name} className="block text-sm">{label}</label>
                    <input {...musicField(name)} type="text" />
                    {feedback(name)}
                  </div>
                ))}
                {musicNumberFields.map(({ name, label, min, max, step }) => (
                  <div key={name} className="min-w-0 space-y-1">
                    <label htmlFor={name} className="block text-sm">{label}, {min}–{max}</label>
                    <input {...musicField(name)} type="number" min={min} max={max} step={step} />
                    {feedback(name)}
                  </div>
                ))}
                <div className="min-w-0 space-y-1">
                  <label htmlFor="music_genre" className="block text-sm">Жанр</label>
                  <select {...musicField('music_genre')}>
                    <option value="">Не указан</option>
                    {genres.map((genre) => <option key={genre}>{genre}</option>)}
                  </select>
                  {feedback('music_genre')}
                </div>
                <div className="min-w-0 space-y-1">
                  <label htmlFor="music_mode" className="block text-sm">Лад</label>
                  <select {...musicField('music_mode')}>
                    <option value="">Не указан</option>
                    <option value="major">Мажор</option>
                    <option value="minor">Минор</option>
                  </select>
                  {feedback('music_mode')}
                </div>
              </div>
            </details>
          </section>
          <p id="form-error" role="alert" tabIndex={-1} className={errorStyle}>{errors.form}</p>
          <button type="submit" className="rounded-(--radius-sm) bg-(--color-accent) px-4 py-2.5 font-semibold text-(color:--color-background) disabled:opacity-60">
            {pending ? 'Сохраняем день…' : errors.form ? 'Повторить отправку' : 'Создать открытку'}
          </button>
        </fieldset>
      </form>
      <p role="status" className="sr-only">{pending ? 'Сохраняем день…' : ''}</p>
    </div>
  )
}
