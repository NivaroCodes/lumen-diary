// Слои открытки, нарисованные кодом: растровый свет (вместо градиента), погодная сцена и зерно.
// Всё детерминировано от seed. Без движения (reduced motion или пауза) рисуется один кадр.
import { useEffect, useRef } from 'react'
import type { VisualModel } from './postcard-model'
import type { MotionPlan } from './postcard-motion'
import { lightGeometry, postcardAppearance, sequence } from './postcard-visual'

type Kind = 'light' | 'weather' | 'grain'
type Draw = (ctx: CanvasRenderingContext2D, w: number, h: number, t: number) => void

// Кадр «как в покое»: середина первого цикла, чтобы статичная сцена была содержательной.
const STILL_T = 1234

function lightDraw(visual: VisualModel, plan: MotionPlan): Draw {
  const { x, y } = lightGeometry(visual)
  // Точки — цветом «освещённой бумаги»: тогда расчёт контраста текста (postcard-visual.ts) остаётся строгим.
  const litPaper = String(postcardAppearance(visual).paint['--paper-light'])
  const random = sequence(visual.seed ^ 0x51ed)
  const jitter = Array.from({ length: 4096 }, () => random() - 0.5)
  const intensity = visual.light.intensity
  const drift = plan.scene === 'sun' ? 0.05 + 0.08 * plan.amplitude : 0
  const period = plan.beatMs * 8
  return (ctx, w, h, t) => {
    ctx.clearRect(0, 0, w, h)
    const phase = Math.sin((2 * Math.PI * t) / period)
    const ox = (x + drift * phase) * w
    const oy = (y + drift * 0.5 * Math.cos((2 * Math.PI * t) / period)) * h
    const step = w / 46
    const maxR = step * 0.62 * (0.45 + 0.55 * intensity)
    ctx.fillStyle = litPaper
    let i = 0
    for (let row = 0; row * step < h + step; row++) {
      const offset = row % 2 ? step / 2 : 0 // шахматный растр, как в печати
      for (let col = 0; col * step < w + step; col++) {
        const px = col * step + offset + jitter[i++ % jitter.length] * step * 0.18
        const py = row * step + jitter[i++ % jitter.length] * step * 0.18
        const d = Math.hypot((px - ox) / (0.85 * w), (py - oy) / (0.75 * h))
        const f = Math.max(0, 1 - d) ** 1.5
        const r = maxR * f
        if (r < 0.35) continue
        ctx.beginPath()
        ctx.arc(px, py, r, 0, Math.PI * 2)
        ctx.fill()
      }
    }
  }
}

function weatherDraw(visual: VisualModel, plan: MotionPlan): Draw {
  const random = sequence(visual.seed ^ 0xa11ce)
  const count = 24 + visual.density.elements * 4
  const items = Array.from({ length: count }, () => ({ x: random(), p: random(), s: random(), k: random() }))
  const sharp = plan.character === 'sharp'

  // Ворота ритма для минора: элементы видны в первой половине каждых двух ударов, потом пауза.
  const gate = (t: number, p: number) => {
    if (!sharp) return 1
    const phase = ((t / (plan.beatMs * 2)) + p * 0.25) % 1
    return phase < 0.55 ? 1 : 0
  }

  switch (plan.scene) {
    case 'rain':
      return (ctx, w, h, t) => {
        ctx.clearRect(0, 0, w, h)
        ctx.lineCap = 'round'
        ctx.lineWidth = Math.max(1, w / 420)
        const slant = Math.tan((8 * Math.PI) / 180)
        for (const d of items) {
          const len = h * (0.05 + 0.07 * plan.amplitude) * (0.6 + d.s * 0.8)
          const fall = plan.dropFallMs * (0.85 + d.k * 0.3)
          const y = (((t / fall) + d.p) % 1) * (h + len) - len
          const x = d.x * w * 1.1 - y * slant
          const alpha = gate(t, d.p) * (0.35 + 0.35 * d.s)
          if (!alpha) continue
          ctx.strokeStyle = `rgb(235 244 255 / ${alpha})`
          ctx.beginPath()
          ctx.moveTo(x, y)
          ctx.lineTo(x - len * slant, y + len)
          ctx.stroke()
        }
      }
    case 'snow':
      return (ctx, w, h, t) => {
        ctx.clearRect(0, 0, w, h)
        for (const d of items) {
          const fall = plan.beatMs * 6 * (0.8 + d.k * 0.5)
          const y = (((t / fall) + d.p) % 1) * (h + 10) - 5
          const x = d.x * w + Math.sin(t / plan.beatMs + d.p * 6) * w * 0.02 * (0.5 + plan.amplitude)
          ctx.fillStyle = `rgb(250 250 252 / ${gate(t, d.p) * (0.5 + d.s * 0.4)})`
          ctx.beginPath()
          ctx.arc(x, y, (1 + d.s * 1.8) * (w / 400), 0, Math.PI * 2)
          ctx.fill()
        }
      }
    case 'fog':
    case 'cloud': {
      // Дымка и облака — тоже растр: точки, собранные в полосы или облака, дрейфуют по кадру.
      const fog = plan.scene === 'fog'
      const dots = Array.from({ length: fog ? 1400 : 900 }, () => {
        const band = Math.floor(random() * (fog ? 3 : 4))
        const cx = fog ? random() : (band + 0.5) / 4 + (random() - 0.5) * 0.08
        const cy = fog ? 0.35 + band * 0.22 + (random() - 0.5) * 0.18 : 0.12 + (band % 2) * 0.16 + (random() - 0.5) * 0.12
        const spread = fog ? 0 : (random() - 0.5) * 0.2
        return { x: cx + spread, y: cy, r: random(), band }
      })
      const period = plan.revealMs * (fog ? 6 : 8)
      return (ctx, w, h, t) => {
        ctx.clearRect(0, 0, w, h)
        const shift = (t / period) % 1
        for (const d of dots) {
          const speed = fog ? 0.6 + d.band * 0.25 : 1
          const x = (((d.x + shift * speed) % 1) + 1) % 1
          const alpha = (fog ? 0.22 : 0.3) * gate(t, d.band * 0.3)
          if (!alpha) continue
          ctx.fillStyle = `rgb(232 236 242 / ${alpha})`
          ctx.beginPath()
          ctx.arc(x * w, d.y * h, (fog ? 2.2 : 2.6) * (w / 400) * (0.6 + d.r), 0, Math.PI * 2)
          ctx.fill()
        }
      }
    }
    case 'sun':
      return (ctx, w, h, t) => {
        // Блики на удар пульса около источника света.
        ctx.clearRect(0, 0, w, h)
        const { x, y } = lightGeometry(visual)
        for (const d of items.slice(0, 14)) {
          const pulse = Math.max(0, Math.sin(((t / plan.beatMs) + d.p) * Math.PI))
          const alpha = gate(t, d.p) * pulse * 0.45
          if (alpha < 0.02) continue
          ctx.fillStyle = `rgb(255 244 214 / ${alpha})`
          ctx.beginPath()
          ctx.arc((x + (d.x - 0.5) * 0.6) * w, (y + (d.s - 0.5) * 0.6) * h, (1.5 + d.k * 2.5) * (w / 400), 0, Math.PI * 2)
          ctx.fill()
        }
      }
    default:
      return (ctx, w, h) => ctx.clearRect(0, 0, w, h)
  }
}

function grainDraw(visual: VisualModel): Draw {
  return (ctx, w, h) => {
    const random = sequence(visual.seed ^ 0x6a17)
    ctx.clearRect(0, 0, w, h)
    const count = Math.round((w * h) / 90)
    for (let i = 0; i < count; i++) {
      const light = random() > 0.5
      ctx.fillStyle = light ? 'rgb(255 248 240 / .5)' : 'rgb(0 0 0 / .6)'
      ctx.fillRect(random() * w, random() * h, 1, 1)
    }
  }
}

export default function PostcardScene({ kind, visual, plan, playing, className }: {
  kind: Kind
  visual: VisualModel
  plan: MotionPlan
  playing: boolean
  className: string
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    const ctx = canvas?.getContext('2d')
    if (!canvas || !ctx) return
    const reduced = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false
    const draw = kind === 'light' ? lightDraw(visual, plan) : kind === 'weather' ? weatherDraw(visual, plan) : grainDraw(visual)
    const animated = kind !== 'grain' && playing && !reduced && (kind === 'weather' ? plan.scene !== 'still' : plan.scene === 'sun')

    let frame = 0
    let visible = true
    let start = 0
    const size = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2)
      const { width, height } = canvas.getBoundingClientRect()
      canvas.width = Math.max(1, Math.round(width * dpr))
      canvas.height = Math.max(1, Math.round(height * dpr))
    }
    const paint = (t: number) => draw(ctx, canvas.width, canvas.height, t)
    const loop = (now: number) => {
      if (!start) start = now - STILL_T
      if (visible) paint(now - start)
      frame = requestAnimationFrame(loop)
    }

    size()
    paint(STILL_T)
    const resize = new ResizeObserver(() => { size(); paint(STILL_T) })
    resize.observe(canvas)
    const seen = new IntersectionObserver(([entry]) => { visible = entry.isIntersecting })
    seen.observe(canvas)
    if (animated) frame = requestAnimationFrame(loop)
    return () => {
      cancelAnimationFrame(frame)
      resize.disconnect()
      seen.disconnect()
    }
  }, [kind, visual, plan, playing])

  return <canvas ref={canvasRef} className={className} aria-hidden="true" />
}
