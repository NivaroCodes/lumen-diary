// Подсказки о звучании песни по фразе пользователя. Чистые функции, без побочных эффектов.
// Это оценка по словам, а не измерение звука.

export type Tempo = 'slow' | 'medium' | 'fast'
export type Mode = 'major' | 'minor'
export type HintField = 'tempo_bpm' | 'energy' | 'mode' | 'genre'
export interface HintInfo { field: HintField; source: 'chosen' | 'described' }
export interface MusicChoices { tempo?: Tempo; mode?: Mode; genre?: string }
export interface MusicHints {
  tempo_bpm?: number
  energy?: number
  mode?: Mode
  genre?: string
  hints: HintInfo[]
}

// Корни слов (нижний регистр, ё = е не приводим: перечислены обе формы).
// Корень совпадает с началом слова. Если корень заканчивается на «=», это целое слово
// (допускается окончание до двух букв), чтобы «поп» не находилось в «попробовать».
export const TEMPO_PRESETS: Record<Tempo, { tempo_bpm: number; energy: number }> = {
  slow: { tempo_bpm: 68, energy: 0.25 },
  medium: { tempo_bpm: 100, energy: 0.55 },
  fast: { tempo_bpm: 128, energy: 0.85 },
}

export const TEMPO_KEYWORDS: Record<Tempo, string[]> = {
  slow: ['медлен', 'тих', 'спокой', 'нежн', 'плавн', 'баллад'],
  medium: ['средн', 'умерен'],
  fast: ['энергичн', 'быстр', 'драйв', 'танц', 'бодр', 'динамичн', 'мощн'],
}

export const MODE_KEYWORDS: Record<Mode, string[]> = {
  major: ['светл', 'мажор', 'весёл', 'весел', 'радост', 'солнечн', 'бодр'],
  minor: ['тёмн', 'темн', 'минор', 'груст', 'печальн', 'меланхол', 'тоскл'],
}

export const GENRE_KEYWORDS: Record<string, string[]> = {
  electronic: ['электрон', 'techno', 'house', 'синт'],
  rock: ['рок=', 'гитар'],
  pop: ['поп='],
  ambient: ['ambient', 'эмбиент', 'атмосфер'],
}

function matches(text: string, root: string) {
  const whole = root.endsWith('=')
  const stem = whole ? root.slice(0, -1) : root
  const pattern = new RegExp(`(^|[^а-яёa-z0-9])${stem}${whole ? '[а-яё]{0,2}(?![а-яёa-z0-9])' : ''}`)
  return pattern.test(text)
}

function matched<K extends string>(text: string, table: Record<K, string[]>) {
  return (Object.keys(table) as K[]).filter((key) => table[key].some((root) => matches(text, root)))
}

export function inferMusicHints(description: string, chosen: MusicChoices = {}): MusicHints {
  const text = description.toLowerCase()
  const result: MusicHints = { hints: [] }

  // Явный выбор пользователя важнее слов; противоречивые слова (и «тихо», и «быстро») не угадываем.
  const tempos = chosen.tempo ? [chosen.tempo] : matched(text, TEMPO_KEYWORDS)
  if (tempos.length === 1) {
    const source = chosen.tempo ? 'chosen' : 'described'
    Object.assign(result, TEMPO_PRESETS[tempos[0]])
    result.hints.push({ field: 'tempo_bpm', source }, { field: 'energy', source })
  }

  const modes = chosen.mode ? [chosen.mode] : matched(text, MODE_KEYWORDS)
  if (modes.length === 1) {
    result.mode = modes[0]
    result.hints.push({ field: 'mode', source: chosen.mode ? 'chosen' : 'described' })
  }

  const genres = chosen.genre ? [chosen.genre] : matched(text, GENRE_KEYWORDS)
  if (genres.length === 1) {
    result.genre = genres[0]
    result.hints.push({ field: 'genre', source: chosen.genre ? 'chosen' : 'described' })
  }
  return result
}
