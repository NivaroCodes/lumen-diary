import type { CSSProperties } from 'react'

// Заголовок, проявляющийся по буквам. Слова не разрываются при переносе строки.
export default function Letters({ text, stepMs }: { text: string; stepMs: number }) {
  let index = 0
  return (
    <>
      {text.split(/(\s+)/).map((part, partIndex) => {
        if (!part) return null
        if (/^\s+$/.test(part)) return ' '
        return (
          <span key={partIndex} className="word">
            {Array.from(part).map((letter) => {
              const delay = index++ * stepMs
              return <span key={delay} className="letter" style={{ '--letter-delay': `${delay}ms` } as CSSProperties}>{letter}</span>
            })}
          </span>
        )
      })}
    </>
  )
}
