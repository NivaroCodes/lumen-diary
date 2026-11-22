// Тест названия песни в блоке «Песня дня»: пустое название → «Песня без названия»,
// описание звучания из формы в название не подставляется (issue 2 и 3).
import assert from 'node:assert/strict'
import { createElement as h } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { songTitle } from '../src/days-api.ts'

// 1. Чистая функция: пустое/пробельное/отсутствующее название → запасной текст.
assert.equal(songTitle({ title: '' }), 'Песня без названия')
assert.equal(songTitle({ title: null }), 'Песня без названия')
assert.equal(songTitle({ title: '   ' }), 'Песня без названия')
assert.equal(songTitle({ title: 'U Weren’t Hear Me' }), 'U Weren’t Hear Me')

// 2. Рендер строки названия, как в MemoryPage. При пустом названии блок не содержит описание.
const descriptions = ['медленная и тихая', 'умеренная, грустная, с пианино']
for (const description of descriptions) {
  const music = { title: '', description }
  const html = renderToStaticMarkup(h('p', { className: 'music-desc' }, songTitle(music)))
  assert.ok(html.includes('Песня без названия'), 'показываем запасной текст')
  assert.ok(!html.includes(description), 'блок «Песня дня» не содержит текста описания')
}

console.log('song-title: all checks passed')
