export type Scene = 'rain' | 'fog' | 'snow' | 'sun' | 'cloud' | 'still'
export type Character = 'smooth' | 'sharp' | 'neutral'

export interface VisualModel {
  seed: number
  light: { direction_deg: number; intensity: number; temperature_k: number }
  palette: { colors: string[]; saturation: number }
  density: { value: number; elements: number }
  texture: { grain: number; blur: number; weather: 'none' | 'rain' | 'fog' }
  line: { trajectory: 'rising' | 'falling' | 'wave' | 'flat'; amplitude: number; roughness: number; color_index: number }
  // character и scene (R-MOT-03, R-MOT-04) есть у дней, созданных после их появления.
  motion?: { reveal_ms: number; pulse_ms: number; character?: Character; scene?: Scene }
  contrast: number
  caption: string
}

export interface PostcardDay {
  date: string
  photos: string[]
  visual: VisualModel
  place?: string | null
}

export function formatDayDate(date: string) {
  return date.split('-').reverse().join('.')
}

const months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']

// «22 ноября 2026» — дата на открытке.
export function formatLongDate(date: string) {
  const [year, month, day] = date.split('-').map(Number)
  if (!year || !month || !day) return date
  return `${day} ${months[month - 1]} ${year}`
}
