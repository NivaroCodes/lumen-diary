"""Три демо-дня с разным настроением: осенний парк с какао, ночь в офисе перед сдачей, дождливое утро.

Фото рисуются кодом (Pillow), чужих снимков нет. Дни создаются обычным POST /api/days, как из формы.
Темп, энергия, лад и жанр — те же значения, что фронтенд выводит из фразы о песне (src/music-hints.ts).

Запуск (сервер должен работать):
    python scripts/seed_demo_days.py                 # http://127.0.0.1:8000
    python scripts/seed_demo_days.py --url http://127.0.0.1:8000 --save-photos ../docs/submission/demo-photos
"""
from __future__ import annotations

import argparse
import io
import random
from pathlib import Path

import httpx
from PIL import Image, ImageDraw, ImageFilter

W, H = 1200, 900


def _png(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def park(variant: int) -> Image.Image:
    rnd = random.Random(10 + variant)
    img = Image.new("RGB", (W, H), (226, 206, 160))
    d = ImageDraw.Draw(img)
    d.rectangle([0, int(H * 0.62), W, H], fill=(176, 120, 58))  # дорожка в листьях
    for _ in range(9):  # стволы
        x = rnd.randint(-40, W)
        d.rectangle([x, 0, x + rnd.randint(22, 46), int(H * 0.7)], fill=(74, 48, 32))
    for _ in range(260):  # листва и листья на земле
        x, y = rnd.randint(-60, W), rnd.randint(-60, int(H * 0.55)) if rnd.random() < .7 else rnd.randint(int(H * .6), H)
        r = rnd.randint(10, 46)
        color = rnd.choice([(214, 120, 40), (232, 170, 54), (186, 70, 36), (240, 196, 92), (150, 90, 40)])
        d.ellipse([x - r, y - r * .7, x + r, y + r * .7], fill=color)
    if variant == 1:  # стакан какао
        d.rounded_rectangle([W * .42, H * .38, W * .58, H * .86], radius=26, fill=(238, 228, 210))
        d.ellipse([W * .42, H * .34, W * .58, H * .44], fill=(96, 56, 34))
        d.rectangle([W * .42, H * .55, W * .58, H * .66], fill=(150, 98, 60))
    return img.filter(ImageFilter.GaussianBlur(1.2))


def office(variant: int) -> Image.Image:
    rnd = random.Random(20 + variant)
    img = Image.new("RGB", (W, H), (14, 18, 34))
    d = ImageDraw.Draw(img)
    for row in range(8):  # окна соседних зданий
        for col in range(16):
            if rnd.random() < .22:
                x, y = 30 + col * 72, 30 + row * 60
                d.rectangle([x, y, x + 40, y + 30], fill=rnd.choice([(250, 198, 110), (236, 170, 80), (120, 150, 210)]))
    d.rectangle([0, int(H * .7), W, H], fill=(28, 26, 30))  # стол
    if variant == 0:  # монитор
        d.rectangle([W * .28, H * .36, W * .72, H * .72], fill=(40, 70, 120))
        for i in range(9):
            d.rectangle([W * .31, H * .40 + i * 26, W * (.4 + rnd.random() * .28), H * .40 + i * 26 + 10], fill=(150, 200, 240))
    else:  # лампа и кружка
        d.ellipse([W * .12, H * .45, W * .38, H * .75], fill=(255, 196, 110))
        d.rounded_rectangle([W * .62, H * .58, W * .72, H * .78], radius=12, fill=(220, 220, 228))
    return img.filter(ImageFilter.GaussianBlur(1.6))


def rain(variant: int) -> Image.Image:
    rnd = random.Random(30 + variant)
    img = Image.new("RGB", (W, H), (148, 162, 176))
    d = ImageDraw.Draw(img)
    for i in range(6):  # крыши
        x = i * 220 - 40
        d.polygon([(x, H * .55), (x + 110, H * .32 + rnd.randint(-30, 30)), (x + 230, H * .55)], fill=(92, 104, 118))
    d.rectangle([0, int(H * .55), W, H], fill=(70, 80, 92))  # мокрая улица
    for _ in range(14):  # отражения фонарей в лужах
        x, y = rnd.randint(0, W), rnd.randint(int(H * .62), H)
        d.ellipse([x - 40, y - 8, x + 40, y + 8], fill=(214, 196, 140))
    for _ in range(420):  # струи дождя
        x, y = rnd.randint(0, W), rnd.randint(0, H)
        d.line([x, y, x - 6, y + 40], fill=(206, 216, 228), width=2)
    if variant == 1:  # зонт
        cx, cy = W * .5, H * .5
        d.pieslice([cx - 170, cy - 120, cx + 170, cy + 120], 180, 360, fill=(46, 58, 74))
        d.line([cx, cy, cx, cy + 190], fill=(46, 58, 74), width=8)
    return img.filter(ImageFilter.GaussianBlur(1.0))


DAYS = [
    {
        "key": "park",
        "date": "2026-10-18",
        "text": ("Парк днём был жёлто-красным. Листья шуршали под ногами, мы купили какао в бумажных стаканах "
                 "и сели на скамейку у пруда. Солнце грело сквозь клёны. Говорили о пустяках и смеялись."),
        "photos": [park(0), park(1), park(2)],
        "place": "Парк у пруда",
        "weather": "sun",
        # Реальный трек из Spotify; название как в Spotify.
        "music": {"music_url": "https://open.spotify.com/track/61iJknbAXSuBflDz3vSQ0b",
                  "music_title": "U Weren't Here I Really Miss You",
                  "music_description": "медленная, светлая, тёплая акустика",
                  # inferMusicHints: «медлен» → 68 BPM, энергия 0.25; «светл» → мажор
                  "music_tempo_bpm": "68", "music_energy": "0.25", "music_mode": "major"},
    },
    {
        "key": "office",
        "date": "2026-11-21",
        "text": ("Офис ночью совсем пустой, только наш стол и огни города за стеклом. Завтра сдача. "
                 "Работали без перерыва. Написали последние тесты. Сделали открытку заново. Отправили сборку. "
                 "Позвонили команде. Поужинали холодной пиццей. Кофе остыл. "
                 "В три часа ночи всё заработало, и мы посмотрели друг на друга молча."),
        "photos": [office(0), office(1)],
        "place": "Офис команды",
        "weather": None,
        # Ссылка на песню НЕ выбрана: плеер не показывается. Проигрывание добавит команда.
        "music": {"music_url": "https://example.com/song-not-chosen",
                  "music_description": "быстрая, энергичная электроника, тёмная",
                  # «быстр» → 128 BPM, 0.85; «тёмн» → минор; «электрон» → electronic
                  "music_tempo_bpm": "128", "music_energy": "0.85", "music_mode": "minor",
                  "music_genre": "electronic"},
    },
    {
        "key": "rain",
        "date": "2026-11-12",
        "text": ("Утром шёл дождь. Проснулась раньше будильника, заварила чай и долго смотрела в окно на мокрые крыши. "
                 "Пошла на работу под зонтом, в лужах отражались фонари."),
        "photos": [rain(0), rain(1)],
        "place": None,
        "weather": "rain",
        # Ссылка на песню НЕ выбрана: плеер не показывается. Проигрывание добавит команда.
        "music": {"music_url": "https://example.com/song-not-chosen",
                  "music_description": "умеренная, грустная, с пианино",
                  # «умерен» → 100 BPM, 0.55; «груст» → минор; пианино жанр не задаёт
                  "music_tempo_bpm": "100", "music_energy": "0.55", "music_mode": "minor"},
    },
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--save-photos", type=Path, default=None, help="Папка, куда сохранить нарисованные фото")
    args = parser.parse_args()

    for day in DAYS:
        fields = {"text": day["text"], "date": day["date"], **day["music"]}
        if day["place"]:
            fields["place"] = day["place"]
        if day["weather"]:
            fields["weather"] = day["weather"]
        files = [("photos", (f"{day['key']}-{i + 1}.png", _png(img), "image/png")) for i, img in enumerate(day["photos"])]
        if args.save_photos:
            args.save_photos.mkdir(parents=True, exist_ok=True)
            for i, img in enumerate(day["photos"]):
                img.save(args.save_photos / f"{day['key']}-{i + 1}.jpg", quality=86)
        resp = httpx.post(f"{args.url}/api/days", data=fields, files=files, timeout=60)
        resp.raise_for_status()
        body = resp.json()
        print(f"{day['key']:7} {body['title']:28} папка: {body['folder']}   id: {body['id']}")


if __name__ == "__main__":
    main()
