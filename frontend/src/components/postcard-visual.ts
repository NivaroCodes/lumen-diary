import type { VisualModel } from './postcard-model'

type Rgb = readonly [number, number, number]
type LuminanceRange = readonly [number, number]
type Zone = readonly [x: number, y: number, width: number, height: number]

// Fractions of the 1080 × 1350 canvas. Matches the paper gradient and text zones in postcard.css.
const paperRadius = [0.85, 0.75] as const
const dateZone: Zone = [72 / 1080, 72 / 1350, 936 / 1080, 28.08 / 1350]
const titleZone: Zone = [72 / 1080, 1072 / 1350, 936 / 1080, 156 / 1350]
const signatureZone: Zone = [72 / 1080, 1260 / 1350, 936 / 1080, 28.08 / 1350]
const lineZone: Zone = [72 / 1080, 870 / 1350, 936 / 1080, 180 / 1350]

const charcoal = [22, 23, 27] as const
const preferredInk = [248, 238, 227] as const
const black = [0, 0, 0] as const
const white = [255, 255, 255] as const

function hexToRgb(hex: string): Rgb {
  const value = Number.parseInt(hex.slice(1), 16)
  return [value >> 16 & 255, value >> 8 & 255, value & 255]
}

function cssRgb([red, green, blue]: Rgb) {
  return `rgb(${red} ${green} ${blue})`
}

function mix(from: Rgb, to: Rgb, amount: number, round = Math.round): Rgb {
  const channel = (index: 0 | 1 | 2) => round(from[index] + (to[index] - from[index]) * amount)
  return [channel(0), channel(1), channel(2)]
}

function luminance([red, green, blue]: Rgb) {
  function linear(value: number) {
    const channel = value / 255
    return channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4
  }
  return 0.2126 * linear(red) + 0.7152 * linear(green) + 0.0722 * linear(blue)
}

function contrastAgainstRange(color: Rgb, [dark, light]: LuminanceRange) {
  const ink = luminance(color)
  const closest = Math.max(dark, Math.min(ink, light))
  return (Math.max(closest, ink) + 0.05) / (Math.min(closest, ink) + 0.05)
}

function zoneLuminance(paper: Rgb, litPaper: Rgb, [cx, cy]: readonly [number, number], [x, y, width, height]: Zone): LuminanceRange {
  function distance(dx: number, dy: number) {
    return Math.min(1, Math.hypot(dx / paperRadius[0], dy / paperRadius[1]))
  }

  const near = distance(Math.max(x - cx, 0, cx - x - width), Math.max(y - cy, 0, cy - y - height))
  const far = distance(Math.max(Math.abs(x - cx), Math.abs(x + width - cx)), Math.max(Math.abs(y - cy), Math.abs(y + height - cy)))
  // The opaque sRGB stops are monotonic in all channels. Round outward for a conservative bound.
  return [luminance(mix(litPaper, paper, far, Math.floor)), luminance(mix(litPaper, paper, near, Math.ceil))]
}

function chooseTextColor(range: LuminanceRange) {
  if (contrastAgainstRange(preferredInk, range) >= 4.5) return preferredInk
  const dark = contrastAgainstRange(black, range)
  const light = contrastAgainstRange(white, range)
  if (Math.max(dark, light) < 4.5) return null
  return dark >= light ? black : white
}

function textStyles(sharedColor: Rgb | null, range: LuminanceRange) {
  const color = sharedColor ?? chooseTextColor(range)
  if (color) return { color: cssRgb(color) }

  // An opaque neutral surface guarantees contrast even when the gradient crosses both thresholds.
  return { color: cssRgb(black), backgroundColor: cssRgb(preferredInk) }
}

export function sequence(seed: number) {
  let state = seed >>> 0
  return () => {
    state = (Math.imul(state, 1664525) + 1013904223) >>> 0
    return state / 4294967296
  }
}

export function buildLine({ trajectory, amplitude, roughness }: VisualModel['line'], seed: number) {
  const random = sequence(seed ^ 0x9e3779b9)
  const profiles = {
    rising: (t: number) => 1 - 2 * t,
    falling: (t: number) => 2 * t - 1,
    wave: (t: number) => Math.sin(4 * Math.PI * t),
    flat: () => 0,
  }
  const points = Array.from({ length: 25 }, (_, index) => {
    const t = index / 24
    const jitter = (2 * random() - 1) * (4 + 8 * amplitude) * roughness * Math.sin(Math.PI * t)
    return {
      x: 8 + t * 920,
      y: 90 + profiles[trajectory](t) * (12 + 48 * amplitude) + jitter,
    }
  })

  const format = ({ x, y }: (typeof points)[number]) => `${x.toFixed(1)} ${y.toFixed(1)}`
  const segments = points.slice(1, -1).map((point, index) => {
    const next = points[index + 2]
    const midpoint = { x: (point.x + next.x) / 2, y: (point.y + next.y) / 2 }
    return `Q${format(point)} ${format(midpoint)}`
  })
  return [`M${format(points[0])}`, ...segments, `L${format(points[points.length - 1])}`].join(' ')
}

// Источник света в долях открытки и цвет света по температуре (R-LIGHT-01, R-LIGHT-03).
export function lightGeometry({ light }: VisualModel) {
  const temperature = (light.temperature_k - 2700) / 3800
  const tint = mix([255, 192, 120], [189, 220, 255], temperature)
  const radians = light.direction_deg * Math.PI / 180
  return { x: 0.5 - 0.5 * Math.sin(radians), y: 0.5 - 0.5 * Math.cos(radians), tint }
}

export function postcardAppearance({ palette, light, line, contrast }: VisualModel) {
  const colors = palette.colors
  const paper = mix(charcoal, hexToRgb(colors[0]), 0.30)
  const temperature = (light.temperature_k - 2700) / 3800
  const tint = mix([255, 192, 120], [189, 220, 255], temperature)
  const strength = 0.10 + 0.45 * light.intensity
  const screen = (index: 0 | 1 | 2) => Math.round(paper[index] + (255 - paper[index]) * tint[index] / 255 * strength)
  const litPaper: Rgb = [screen(0), screen(1), screen(2)]
  const radians = light.direction_deg * Math.PI / 180
  const x = Number((50 - 50 * Math.sin(radians)).toFixed(1))
  const y = Number((50 - 50 * Math.cos(radians)).toFixed(1))
  const origin = [x / 100, y / 100] as const

  const dateRange = zoneLuminance(paper, litPaper, origin, dateZone)
  const titleRange = zoneLuminance(paper, litPaper, origin, titleZone)
  const signatureRange = zoneLuminance(paper, litPaper, origin, signatureZone)
  const sharedInk = chooseTextColor([
    Math.min(dateRange[0], titleRange[0], signatureRange[0]),
    Math.max(dateRange[1], titleRange[1], signatureRange[1]),
  ])

  const paletteStroke = mix(hexToRgb(colors[line.color_index] ?? colors[0]), preferredInk, 0.35)
  const lineRange = zoneLuminance(paper, litPaper, origin, lineZone)
  const lineColor = [paletteStroke, mix(paletteStroke, white, 0.55), mix(paletteStroke, black, 0.55), white, black]
    .find((color) => contrastAgainstRange(color, lineRange) >= 3) ?? white

  return {
    paint: {
      '--paper-color': cssRgb(paper),
      '--paper-light': cssRgb(litPaper),
      '--paper-radius': paperRadius.map((radius) => `${radius * 100}%`).join(' '),
      '--frame-color': colors[1] ?? colors[0],
      '--mark-color': colors[2] ?? colors[0],
      '--line-color': cssRgb(lineColor),
      '--line-outline': cssRgb(contrastAgainstRange(lineColor, [0, 0]) >= 3 ? black : white),
      '--light-origin': `${x}% ${y}%`,
      '--light-color': `rgb(${tint.join(' ')} / ${0.13 + 0.42 * light.intensity})`,
      '--photo-brightness': 0.73 + 0.46 * light.intensity,
      '--photo-contrast': 0.75 + 0.55 * contrast,
      '--photo-saturation': 0.66 + 0.8 * palette.saturation,
    },
    date: textStyles(sharedInk, dateRange),
    title: textStyles(sharedInk, titleRange),
    signature: textStyles(sharedInk, signatureRange),
  }
}
