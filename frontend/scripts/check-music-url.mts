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
