import type { CSSProperties } from 'react'
import DayPhoto from './DayPhoto'
import { formatDayDate } from './postcard-model'
import type { PostcardDay, VisualModel } from './postcard-model'
import { buildLine, postcardAppearance, sequence } from './postcard-visual'
import './postcard.css'

function buildMarks({ value, elements }: VisualModel['density'], seed: number) {
  const random = sequence(seed)
  return Array.from({ length: elements }, (_, index) => {
    const x = 24 + (index / Math.max(1, elements - 1)) * (650 + value * 115)
    const height = (10 + random() * 25) * (1 + value * 2)
    return { x, height, width: 10 + random() * 14, opacity: 0.3 + random() * 0.4 }
  })
}

export default function Postcard({ day }: { day: PostcardDay }) {
  const { visual, date, photos } = day
  const { density, texture, line, seed } = visual
  const appearance = postcardAppearance(visual)
  const marks = buildMarks(density, seed)
  const styles = {
    ...appearance.paint,
    '--grain-opacity': 0.05 + texture.grain * 0.3,
    '--photo-blur': `${texture.blur * 1.2}px`,
  } as CSSProperties
  const path = buildLine(line, seed)

  return (
    <article className="postcard" aria-label="Открытка дня" style={styles}>
      <time className="postcard-date" dateTime={date} style={appearance.date}>{formatDayDate(date)}</time>
      <div className="postcard-frame" data-weather={texture.weather}>
        <div className="postcard-photos" data-count={photos.length}>
          {photos.map((src, index) => <DayPhoto key={src} src={src} alt={`Фото дня ${index + 1}`} />)}
          {!photos.length && <DayPhoto src={null} alt="" />}
        </div>
        <div className="postcard-light" aria-hidden="true" />
        <div className="postcard-grain" aria-hidden="true" />
        <div className="postcard-weather" aria-hidden="true" />
        <svg className="postcard-marks" viewBox="0 0 936 660" preserveAspectRatio="none" aria-hidden="true">
          {marks.map(({ x, height, width, opacity }) => (
            <rect key={x} x={x} y={616 - height} height={height} width={width} opacity={opacity} />
          ))}
        </svg>
      </div>
      <svg className="postcard-line" viewBox="0 0 936 180" aria-hidden="true">
        <path className="postcard-line-outline" d={path} />
        <path className="postcard-line-stroke" d={path} />
      </svg>
      <h2 className="postcard-title" style={appearance.title}><span>{visual.caption}</span></h2>
      <p className="postcard-signature" style={appearance.signature}>LUMEN DIARY</p>
    </article>
  )
}
