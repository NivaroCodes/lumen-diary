# Таблица «признак → параметр» (v1)

Статус: предложение для согласования (TEAM-02). Правила нумеруются и используются в `explain`. Каждое правило покрывается тестом BE-08.

| ID | Признак | Параметр | Правило (v1) |
|---|---|---|---|
| R-LIGHT-01 | `text.time_of_day` | `light.direction_deg` | morning → 90; day → 180; evening → 270; night → 0; unknown → 90 |
| R-LIGHT-02 | `photos.brightness` | `light.intensity` | intensity = 0.2 + 0.7 × brightness |
| R-LIGHT-03 | `photos.warmth` | `light.temperature_k` | temperature = 6500 − 3800 × warmth |
| R-PAL-01 | `photos.dominant_colors` | `palette.colors` | до 5 цветов, отсортированы по доле; при одном фото — первые 3 |
| R-PAL-02 | `photos.contrast` | `palette.saturation` | saturation = 0.3 + 0.4 × contrast |
| R-DEN-01 | `text.events_count`, `text.length_words` | `density.value` | value = min(1, 0.1 × events_count + length_words / 300) |
| R-DEN-02 | `density.value` | `density.elements` | elements = round(2 + 10 × value) |
| R-TEX-01 | `text.weather` | `texture.weather` | rain → rain; fog → fog; иначе none |
| R-TEX-02 | `photos.brightness` | `texture.grain` | grain = 0.5 × (1 − brightness) |
| R-TEX-03 | `music.tempo_bpm` | `texture.blur` | 0.6 при tempo < 80; 0.3 при 80–110; 0.1 при > 110; null → 0.1 |
| R-LINE-01 | `text.time_of_day` | `line.trajectory` | morning → rising; day → wave; evening → falling; night → flat; unknown → wave |
| R-LINE-02 | `music.energy` | `line.amplitude` | amplitude = 0.1 + 0.8 × energy; null → 0.3 |
| R-LINE-03 | `music.energy`, `music.genre` | `line.roughness` | roughness = 0.2 + 0.5 × energy; жанр rock или electronic: +0.1 (макс. 1.0) |
| R-LINE-04 | — | `line.color_index` | всегда 0 |
| R-MOT-01 | `music.tempo_bpm` | `motion.reveal_ms` | clamp(4000 − 15 × tempo, 800, 4000); null → 2400 |
| R-MOT-02 | `music.tempo_bpm` | `motion.pulse_ms` | clamp(round(60000 / tempo), 600, 2400); null → 1400 |
| R-CON-01 | `photos.contrast`, `music.mode` | `contrast` | 0.3 + 0.4 × contrast; +0.1 при minor; −0.05 при major; clamp 0–1 |
| R-SEED-01 | все входы | `seed` | первые 4 байта SHA-256 (uint32, big-endian) от канонизированного JSON входов |

Примечание к фикстурам: дробные значения округляются до двух знаков (Decimal, ROUND_HALF_UP). Фикстуры генерируются `backend/scripts/regenerate_fixtures.py`, сравнение в тестах точное.
