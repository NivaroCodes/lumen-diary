import { ImageOff } from 'lucide-react'
import { useState } from 'react'

interface DayPhotoProps {
  src: string | null
  alt: string
  className?: string
  compact?: boolean
}

export default function DayPhoto({ src, alt, className = '', compact = false }: DayPhotoProps) {
  const [failedSource, setFailedSource] = useState<string | null>(null)
  const unavailable = !src || src === failedSource

  return (
    <span className={`day-photo relative block min-h-0 min-w-0 overflow-hidden bg-(--color-border) ${className}`}>
      {unavailable ? (
        <span className="day-photo-fallback absolute inset-0 grid content-center justify-items-center gap-1 px-1 text-center text-xs text-(color:--color-text)">
          <ImageOff className="size-4" aria-hidden="true" />
          <span className={compact ? 'sr-only' : undefined}>Фото недоступно</span>
        </span>
      ) : (
        <img src={src} alt={alt} loading={compact ? 'lazy' : undefined}
          className="block size-full object-cover" onError={() => setFailedSource(src)} />
      )}
    </span>
  )
}
