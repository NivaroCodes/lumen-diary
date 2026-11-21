export interface VisualModel {
  seed: number
  light: { direction_deg: number; intensity: number; temperature_k: number }
  palette: { colors: string[]; saturation: number }
  density: { value: number; elements: number }
  texture: { grain: number; blur: number; weather: 'none' | 'rain' | 'fog' }
  line: { trajectory: 'rising' | 'falling' | 'wave' | 'flat'; amplitude: number; roughness: number; color_index: number }
  contrast: number
  caption: string
}

export interface PostcardDay {
  date: string
  photos: string[]
  visual: VisualModel
}

export function formatDayDate(date: string) {
  return date.split('-').reverse().join('.')
}
