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
