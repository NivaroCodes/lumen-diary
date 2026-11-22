// Озвучка записи встроенным синтезом речи браузера (speechSynthesis). Без внешних сервисов и чужих голосов.
// По умолчанию выключена. Скорость — от темпа (R-MOT-02), высота — от лада (R-MOT-03), громкость — от энергии.
import { useEffect, useState } from 'react'
import { voiceSettings } from './postcard-motion'
import type { MotionPlan } from './postcard-motion'

export default function SpeakButton({ text, plan, energy }: { text: string; plan: MotionPlan; energy: number | null }) {
  const supported = typeof window !== 'undefined' && 'speechSynthesis' in window
  const [speaking, setSpeaking] = useState(false)

  useEffect(() => () => { if (supported) window.speechSynthesis.cancel() }, [supported])

  if (!supported) return null

  function toggle() {
    const synth = window.speechSynthesis
    if (speaking) {
      synth.cancel()
      setSpeaking(false)
      return
    }
    const utterance = new SpeechSynthesisUtterance(text)
    const settings = voiceSettings(plan, energy)
    Object.assign(utterance, settings)
    utterance.lang = 'ru-RU'
    const voice = synth.getVoices().find((item) => item.lang.toLowerCase().startsWith('ru'))
    if (voice) utterance.voice = voice
    utterance.onend = () => setSpeaking(false)
    utterance.onerror = () => setSpeaking(false)
    synth.cancel()
    synth.speak(utterance)
    setSpeaking(true)
  }

  return (
    <button type="button" className="btn" aria-pressed={speaking} onClick={toggle}>
      {speaking ? 'Остановить чтение' : 'Прочитать запись вслух'}
    </button>
  )
}
