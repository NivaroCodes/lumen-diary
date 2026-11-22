// Проверка normalizeMusicUrl: node scripts/check-music-url.mts
import assert from 'node:assert/strict'
import { normalizeMusicUrl } from '../src/days-api.ts'

const id = 'https://open.spotify.com/track/61iJknbAXSuBflDz3vSQ0b'
assert.equal(normalizeMusicUrl(`${id}?si=ppu14dO3TqSv3c6bdyeMzQ&utm_source=copy-link`), id)
assert.equal(normalizeMusicUrl(`${id}#frag`), id)
assert.equal(normalizeMusicUrl('https://example.com/song-calm'), 'https://example.com/song-calm')
assert.equal(normalizeMusicUrl('https://open.spotify.com/album/abc?si=1'), 'https://open.spotify.com/album/abc?si=1')
assert.equal(normalizeMusicUrl('не ссылка'), 'не ссылка')
console.log('music-url: all checks passed')

import { musicEmbed } from '../src/days-api.ts'
assert.equal(musicEmbed('https://open.spotify.com/track/61iJknbAXSuBflDz3vSQ0b?si=x')?.src, 'https://open.spotify.com/embed/track/61iJknbAXSuBflDz3vSQ0b')
assert.equal(musicEmbed('https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=10')?.src, 'https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ')
assert.equal(musicEmbed('https://youtu.be/dQw4w9WgXcQ')?.kind, 'youtube')
assert.equal(musicEmbed('https://example.com/song'), null)
assert.equal(musicEmbed('не ссылка'), null)
console.log('music-embed: all checks passed')
