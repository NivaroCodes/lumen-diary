import type { VisualModel } from './components/postcard-model'

export class DayApiError extends Error {
  readonly status: number
  readonly field?: string

  constructor(message: string, status: number, field?: string) {
    super(message)
    this.status = status
    this.field = field
  }
}

export async function createDay(body: FormData) {
  const response = await fetch('/api/days', { method: 'POST', body })
  if (!response.ok) {
    const error = await response.json().catch(() => null) as { message?: unknown; field?: unknown } | null
    const field = typeof error?.field === 'string' ? error.field : undefined
    const message = typeof error?.message === 'string' ? error.message : (
      response.status === 404 ? 'Запись не найдена.' : 'Сервер не смог обработать запрос. Попробуйте ещё раз.'
    )
    throw new DayApiError(message, response.status, field)
  }
  if (response.status !== 201) {
    throw new DayApiError('Сервер не подтвердил создание записи.', response.status)
  }
  const day = await response.json().catch(() => null) as { id?: unknown } | null
  if (typeof day?.id !== 'string' || !day.id.trim()) {
    throw new DayApiError('Сервер не вернул идентификатор записи.', response.status)
  }
  return { id: day.id }
}

export interface DaySummary {
  id: string
  title: string
  date: string
  preview_url: string | null
  folder?: string | null
  place?: string | null
  photos?: string[]
  visual?: VisualModel | null
}

export interface MusicRecord {
  type?: string
  url?: string
  description?: string
  title?: string | null
  artist?: string | null
  genre?: string | null
  tempo_bpm?: number | null
  energy?: number | null
  mode?: 'major' | 'minor' | 'unknown'
  year?: number | null
}

export interface ExplainItem {
  param: string
  value?: unknown
  text_ru: string
  rule?: string
  source?: string
  input?: unknown
  provenance?: 'measured' | 'entered' | 'unknown' | string
}

export interface DayContext {
  weather?: 'rain' | 'fog' | 'cloud' | 'sun' | null
  weather_source?: 'chosen' | 'text'
  place?: string | null
}

export interface DayRecord {
  id: string
  title: string
  date: string
  folder?: string | null
  text: string
  photos: string[]
  music: MusicRecord
  visual: VisualModel
  explain: ExplainItem[]
  profile: Record<string, unknown> & { context?: DayContext }
}

const requestTimeoutMs = 10_000

function isAbortError(error: unknown) {
  return typeof error === 'object' && error !== null && (error as { name?: unknown }).name === 'AbortError'
}

// Общий GET: таймаут, ошибки сети и разбор JSON превращаются в DayApiError, а не в падение страницы.
async function getJson(url: string): Promise<unknown> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), requestTimeoutMs)
  const timeoutMessage = 'Сервер не ответил за 10 секунд. Попробуйте ещё раз.'
  try {
    let response: Response
    try {
      response = await fetch(url, { headers: { Accept: 'application/json' }, signal: controller.signal })
    } catch (error) {
      throw isAbortError(error)
        ? new DayApiError(timeoutMessage, 0)
        : new DayApiError('Не удалось связаться с сервером. Попробуйте ещё раз.', 0)
    }
    if (!response.ok) {
      const error = await response.json().catch(() => null) as { message?: unknown } | null
      const message = typeof error?.message === 'string' ? error.message : (
        response.status === 404 ? 'Запись не найдена.' : 'Сервер не смог обработать запрос. Попробуйте ещё раз.'
      )
      throw new DayApiError(message, response.status)
    }
    try {
      return await response.json()
    } catch (error) {
      throw isAbortError(error)
        ? new DayApiError(timeoutMessage, response.status)
        : new DayApiError('Сервер вернул некорректные данные.', response.status)
    }
  } finally {
    clearTimeout(timer)
  }
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function isDaySummary(value: unknown): value is DaySummary {
  return isObject(value)
    && typeof value.id === 'string'
    && typeof value.title === 'string'
    && typeof value.date === 'string'
    && (typeof value.preview_url === 'string' || value.preview_url === null)
}

function isDayRecord(value: unknown): value is DayRecord {
  return isObject(value)
    && typeof value.id === 'string'
    && typeof value.title === 'string'
    && typeof value.date === 'string'
    && typeof value.text === 'string'
    && Array.isArray(value.photos)
    && value.photos.every((photo) => typeof photo === 'string')
    && isObject(value.music)
    && isObject(value.visual)
    && Array.isArray(value.explain)
    && value.explain.every((item) => isObject(item) && typeof item.param === 'string' && typeof item.text_ru === 'string')
    && isObject(value.profile)
}

export async function getDay(id: string): Promise<DayRecord> {
  const data = await getJson(`/api/days/${encodeURIComponent(id)}`)
  if (!isDayRecord(data)) throw new DayApiError('Сервер вернул некорректные данные.', 0)
  return data
}

export async function listDays(): Promise<DaySummary[]> {
  const data = await getJson('/api/days?sort=date_desc')
  if (!Array.isArray(data) || !data.every(isDaySummary)) {
    throw new DayApiError('Сервер вернул некорректные данные.', 0)
  }
  return data
}

export function errorMessage(error: unknown) {
  return error instanceof DayApiError ? error.message : 'Не удалось связаться с сервером. Попробуйте ещё раз.'
}

export function isMusicUrl(value: string) {
  if (!/^https?:\/\/[^\s]+$/i.test(value)) return false
  try {
    return Boolean(new URL(value).hostname)
  } catch {
    return false
  }
}

// Ссылка на трек Spotify: убираем query и фрагмент (?si=…, utm_*), оставляем /track/<id>. Остальное не меняем.
export function normalizeMusicUrl(url: string): string {
  try {
    const parsed = new URL(url)
    if (parsed.protocol !== 'https:' || parsed.hostname !== 'open.spotify.com') return url
    const match = /^\/track\/([A-Za-z0-9]+)\/?$/.exec(parsed.pathname)
    return match ? `https://open.spotify.com/track/${match[1]}` : url
  } catch {
    return url
  }
}

export type MusicEmbed = { kind: 'spotify' | 'youtube'; src: string; title: string }

// Встраиваемый плеер по ссылке: трек Spotify или видео YouTube (без cookie). Другие ссылки — без плеера.
export function musicEmbed(url: string | undefined): MusicEmbed | null {
  try {
    const parsed = new URL(url ?? '')
    const host = parsed.hostname.replace(/^www\./, '').replace(/^m\./, '')
    if (host === 'open.spotify.com') {
      const match = /^(?:\/intl-[a-z]{2})?\/track\/([A-Za-z0-9]+)\/?$/.exec(parsed.pathname)
      return match ? { kind: 'spotify', src: `https://open.spotify.com/embed/track/${match[1]}`, title: 'Проигрыватель Spotify' } : null
    }
    let id: string | null = null
    if (host === 'youtu.be') id = parsed.pathname.slice(1).split('/')[0]
    if (host === 'youtube.com' || host === 'music.youtube.com') {
      id = parsed.searchParams.get('v') ?? /^\/(?:shorts|embed)\/([\w-]+)/.exec(parsed.pathname)?.[1] ?? null
    }
    return id && /^[\w-]{6,20}$/.test(id)
      ? { kind: 'youtube', src: `https://www.youtube-nocookie.com/embed/${id}`, title: 'Проигрыватель YouTube' }
      : null
  } catch {
    return null
  }
}
