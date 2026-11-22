// План движения открытки. Чистая функция: все числа выводятся из VisualModel по правилам visual_model.py.
import type { Character, Scene, VisualModel } from './postcard-model'

export interface MotionPlan {
  beatMs: number // R-MOT-02: один удар пульса песни
  revealMs: number // R-MOT-01: длина проявки
  letterStepMs: number // шаг букв заголовка, доля проявки
  photoStepMs: number // фото проявляются по одному на удар
  dropFallMs: number // капля пересекает кадр за 1,5 удара
  breathMs: number // один «вдох» линии — 4 удара
  sway: number // размах колебания линии, единицы viewBox (R-LINE-02)
  amplitude: number
  character: Character
  scene: Scene
  ease: string
  notes: { rule: string; text: string }[]
}

const clamp = (value: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, value))

export function sceneOf(visual: VisualModel): Scene {
  if (visual.motion?.scene) return visual.motion.scene
  return visual.texture.weather === 'none' ? 'still' : visual.texture.weather
}

export function motionPlan(visual: VisualModel, titleLength = visual.caption.length): MotionPlan {
  const beatMs = visual.motion?.pulse_ms ?? 1400
  const revealMs = visual.motion?.reveal_ms ?? 2400
  const amplitude = visual.line.amplitude
  const character = visual.motion?.character ?? 'neutral'
  const scene = sceneOf(visual)
  const letterStepMs = Math.round(clamp((revealMs * 0.6) / Math.max(1, titleLength), 20, 120))
  const photoStepMs = beatMs
  const dropFallMs = Math.round(beatMs * 1.5)
  // Минор: волны реже (вдох на 8 ударов) и с паузой; мажор и нейтральный — на 4 удара.
  const breathMs = character === 'sharp' ? beatMs * 8 : beatMs * 4
  const sway = Math.round(4 + 40 * amplitude)
  const ease = character === 'smooth' ? 'cubic-bezier(.45, 0, .55, 1)'
    : character === 'sharp' ? 'cubic-bezier(.9, 0, .1, 1)' : 'ease-in-out'

  const bpm = Math.round(60000 / beatMs)
  const notes = [
    { rule: 'R-MOT-01', text: `Открытка проявляется за ${revealMs} мс; буквы заголовка — с шагом ${letterStepMs} мс.` },
    { rule: 'R-MOT-02', text: `Пульс ${beatMs} мс (около ${bpm} ударов в минуту): фото проявляются по одному на удар.` },
    { rule: 'R-LINE-02', text: `Энергия ${amplitude.toFixed(2)} задаёт размах колебания линии: ${sway} ед.; один вдох длится ${breathMs} мс.` },
    {
      rule: 'R-MOT-03',
      text: character === 'smooth' ? 'Мажор: линия и сцена движутся плавно, без остановок.'
        : character === 'sharp' ? 'Минор: движение резкое и реже, между волнами есть пауза.'
          : 'Лад неизвестен: движение нейтральное.',
    },
    {
      rule: 'R-MOT-04',
      text: {
        rain: `Дождь: капля пересекает кадр за ${dropFallMs} мс (полтора удара).`,
        fog: `Туман: дымка дрейфует, один проход за ${Math.round(revealMs * 6 / 1000)} с.`,
        snow: `Снег: снежинка опускается за ${Math.round(beatMs * 6 / 1000)} с.`,
        sun: `Солнце: пятно света смещается, один цикл за ${Math.round(beatMs * 8 / 1000)} с.`,
        cloud: `Облака: проходят по кадру за ${Math.round(revealMs * 8 / 1000)} с.`,
        still: 'Погоды нет: фон неподвижен, двигаются только линия и свет проявки.',
      }[scene],
    },
  ]
  return { beatMs, revealMs, letterStepMs, photoStepMs, dropFallMs, breathMs, sway, amplitude, character, scene, ease, notes }
}

// Голос озвучки: скорость от темпа (R-MOT-02), высота от лада (R-MOT-03), громкость от энергии.
export function voiceSettings(plan: MotionPlan, energy: number | null) {
  const bpm = 60000 / plan.beatMs
  const rate = Math.min(1.2, Math.max(0.75, 0.8 + ((bpm - 68) / 60) * 0.35))
  const pitch = plan.character === 'smooth' ? 1.05 : plan.character === 'sharp' ? 0.9 : 1
  const volume = energy === null ? 0.85 : 0.6 + 0.4 * energy
  return { rate: Number(rate.toFixed(2)), pitch, volume: Number(volume.toFixed(2)) }
}
