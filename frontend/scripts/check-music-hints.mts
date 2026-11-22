// Проверка inferMusicHints без тестового раннера: node scripts/check-music-hints.mts
import assert from 'node:assert/strict'
import { inferMusicHints } from '../src/music-hints.ts'

const pick = (r: ReturnType<typeof inferMusicHints>) => { const { hints: _h, ...rest } = r; return rest }

assert.deepEqual(pick(inferMusicHints('')), {})
assert.deepEqual(pick(inferMusicHints('медленная и тихая песня')), { tempo_bpm: 68, energy: 0.25 })
assert.deepEqual(pick(inferMusicHints('энергичная электронная музыка')), { tempo_bpm: 128, energy: 0.85, genre: 'electronic' })
assert.equal(inferMusicHints('светлая мажорная').mode, 'major')
assert.equal(inferMusicHints('тёмная, минорная').mode, 'minor')
assert.equal(inferMusicHints('грустная').mode, 'minor')
// явный выбор важнее слов
const o = inferMusicHints('медленная и тёмная', { tempo: 'fast', mode: 'major' })
assert.deepEqual(pick(o), { tempo_bpm: 128, energy: 0.85, mode: 'major' })
assert.deepEqual(o.hints.map((h) => h.source), ['chosen', 'chosen', 'chosen'])
assert.equal(inferMusicHints('медленная').hints[0].source, 'described')
// нет совпадений, пианино не жанр, «стихи» не «тихо», «попробуй» не поп
assert.deepEqual(pick(inferMusicHints('с пианино')), {})
assert.deepEqual(pick(inferMusicHints('стихи, попробовать')), {})
assert.equal(inferMusicHints('поп-песня с гитарой').genre, undefined) // поп и рок одновременно: неоднозначно
assert.equal(inferMusicHints('гитарная баллада').genre, 'rock')
// противоречие слов: темп не угадываем
assert.equal(inferMusicHints('тихая и быстрая').tempo_bpm, undefined)
console.log('music-hints: all checks passed')
