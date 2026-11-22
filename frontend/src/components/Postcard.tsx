import { useMemo } from 'react'
import type { CSSProperties } from 'react'
import { DESIGN_RULES } from '../design-rules'
import DayPhoto from './DayPhoto'
import Letters from './Letters'
import PostcardScene from './PostcardScene'
import { formatLongDate } from './postcard-model'
import type { PostcardDay, VisualModel } from './postcard-model'
import { motionPlan } from './postcard-motion'
import { buildLine, postcardAppearance, sequence } from './postcard-visual'
import './postcard.css'

// Группы «Почему так». Слой открытки отмечен группами, к которым относится.
export type WhyGroup = 'color' | 'texture' | 'composition' | 'motion'

function buildMarks({ value, elements }: VisualModel['density'], seed: number) {
  const random = sequence(seed)
  return Array.from({ length: elements }, (_, index) => {
    const x = 24 + (index / Math.max(1, elements - 1)) * (650 + value * 115)
    const height = (10 + random() * 25) * (1 + value * 2)
    return { x, height, width: 10 + random() * 14, opacity: 0.3 + random() * 0.4 }
  })
}

export default function Postcard({ day, reveal = true, playing = true, highlight = null, compact = false }: {
  day: PostcardDay
  reveal?: boolean // проиграть проявку (заголовок по буквам, фото в ритме пульса)
  playing?: boolean // фоновая сцена движется
  highlight?: WhyGroup | null // подсветить слои выбранной группы «Почему так»
  compact?: boolean
}) {
  const { visual, date, photos, place } = day
  const { density, texture, line, seed } = visual
  const appearance = useMemo(() => postcardAppearance(visual), [visual])
  const plan = useMemo(() => motionPlan(visual), [visual])
  const marks = useMemo(() => buildMarks(density, seed), [density, seed])
  const path = useMemo(() => buildLine(line, seed), [line, seed])

  const styles = {
    ...appearance.paint,
    '--grain-opacity': 0.08 + texture.grain * 0.5,
    '--photo-blur': `${texture.blur * 1.2}px`,
    '--reveal-ms': `${plan.revealMs}ms`,
    '--beat-ms': `${plan.beatMs}ms`,
    '--breath-ms': `${plan.breathMs}ms`,
    '--sway': `${plan.sway}px`,
    '--line-ease': plan.ease,
    '--letter-ms': `${Math.min(900, plan.letterStepMs * 8)}ms`,
  } as CSSProperties

  return (
    <article
      className="pc"
      aria-label={`Открытка дня: ${visual.caption}`}
      style={styles}
      data-gradients={DESIGN_RULES.gradients}
      data-reveal={reveal}
      data-playing={playing}
      data-character={plan.character}
      data-scene={plan.scene}
      data-highlight={highlight ?? undefined}
      data-compact={compact}
    >
      {!DESIGN_RULES.gradients && (
        <PostcardScene kind="light" visual={visual} plan={plan} playing={playing} className="pc-light pc-layer" />
      )}
      <p className="pc-date-row" style={appearance.date}>
        <time dateTime={date}>{formatLongDate(date)}</time>
        {place && <span className="pc-place">{place}</span>}
      </p>

      <div className="pc-frame pc-layer" data-groups="color composition">
        <div className="pc-photos" data-count={photos.length}>
          {photos.map((src, index) => (
            <span key={src} className="pc-photo" style={{ '--photo-delay': `${index * plan.photoStepMs}ms` } as CSSProperties}>
              <DayPhoto src={src} alt={compact ? '' : `Фото дня ${index + 1}`} />
            </span>
          ))}
          {!photos.length && <span className="pc-photo"><DayPhoto src={null} alt="" /></span>}
        </div>
        <PostcardScene kind="grain" visual={visual} plan={plan} playing={false} className="pc-grain pc-sub" />
        <PostcardScene kind="weather" visual={visual} plan={plan} playing={playing} className="pc-weather pc-sub" />
        <svg className="pc-marks pc-sub" viewBox="0 0 936 660" preserveAspectRatio="none" aria-hidden="true">
          {marks.map(({ x, height, width, opacity }, index) => (
            <rect key={x} x={x} y={616 - height} height={height} width={width} opacity={opacity}
              style={{ '--mark-delay': `${Math.round(index * plan.revealMs / (2 * marks.length))}ms` } as CSSProperties} />
          ))}
        </svg>
      </div>

      <svg className="pc-line pc-layer" data-groups="composition motion" viewBox="0 0 936 180" aria-hidden="true">
        <g className="pc-line-breath">
          <path className="pc-line-outline" d={path} pathLength={1} />
          <path className="pc-line-stroke" d={path} pathLength={1} />
        </g>
      </svg>

      <h2 className="pc-title" style={appearance.title}>
        <span className="pc-sr">{visual.caption}</span>
        <span aria-hidden="true" className="pc-title-text">
          <Letters text={visual.caption} stepMs={plan.letterStepMs} />
        </span>
      </h2>
      <p className="pc-signature" style={appearance.signature}>Lumen Diary</p>
    </article>
  )
}
