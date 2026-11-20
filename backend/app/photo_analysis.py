"""Анализ фото (BE-04): признаки для DayProfile и очищенные копии без EXIF."""
from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Any

import numpy as np
from PIL import Image, ImageOps

ANALYSIS_SIZE = 256
STORED_MAX_SIDE = 1600
STORED_JPEG_QUALITY = 88
KMEANS_K = 5
KMEANS_ITERATIONS = 10
KMEANS_SEED = 42


@dataclass(frozen=True)
class PhotoAnalysis:
    profile: dict[str, Any]  # раздел photos из DayProfile
    cleaned_jpegs: list[bytes]  # очищенные копии для папки дня (без EXIF)


def load_rgb(data: bytes) -> Image.Image:
    """Открывает, применяет EXIF-поворот и переводит в RGB (прозрачность — на белый фон)."""
    with Image.open(io.BytesIO(data)) as src:
        img = ImageOps.exif_transpose(src)
        img.load()
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        rgba = img.convert("RGBA")
        background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        return Image.alpha_composite(background, rgba).convert("RGB")
    return img.convert("RGB")


def downscale(img: Image.Image, max_side: int) -> Image.Image:
    """Уменьшает по большей стороне до max_side (увеличивать не будем)."""
    out = img.copy()
    out.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    return out


def encode_clean_jpeg(img: Image.Image) -> bytes:
    """Кодирует в JPEG без EXIF, ICC и прочих метаданных: пишем только пиксели."""
    clean = Image.new("RGB", img.size)
    clean.paste(img)
    buf = io.BytesIO()
    clean.save(buf, format="JPEG", quality=STORED_JPEG_QUALITY, optimize=True)
    return buf.getvalue()


def _luma(pixels: np.ndarray) -> np.ndarray:
    return pixels[:, 0] * 0.299 + pixels[:, 1] * 0.587 + pixels[:, 2] * 0.114


def _clamp01(x: float) -> float:
    return float(min(1.0, max(0.0, x)))


def photo_stats(pixels: np.ndarray) -> dict[str, float]:
    """Статистики одного фото по пикселям (N×3, значения 0–255)."""
    luma = _luma(pixels)
    mean_r, mean_b = float(pixels[:, 0].mean()), float(pixels[:, 2].mean())
    return {
        "brightness": _clamp01(float(luma.mean()) / 255.0),
        "contrast": _clamp01(float(luma.std()) / 128.0),
        "warmth": _clamp01(0.5 + (mean_r - mean_b) / 510.0),
    }


def kmeans_colors(pixels: np.ndarray, k: int = KMEANS_K, iterations: int = KMEANS_ITERATIONS) -> list[str]:
    """k-means с фиксированным seed. Возвращает hex по убыванию доли пикселей."""
    data = pixels.astype(np.float64)
    unique = np.unique(pixels.astype(np.uint8), axis=0)
    k = min(k, len(unique))
    rng = np.random.default_rng(KMEANS_SEED)

    # Инициализация k-means++ на детерминированном генераторе.
    centers = np.empty((k, 3))
    centers[0] = data[rng.integers(len(data))]
    dist = ((data - centers[0]) ** 2).sum(axis=1)
    for i in range(1, k):
        total = dist.sum()
        if total <= 0:
            centers[i] = unique[rng.integers(len(unique))]
        else:
            centers[i] = data[rng.choice(len(data), p=dist / total)]
        dist = np.minimum(dist, ((data - centers[i]) ** 2).sum(axis=1))

    labels = np.zeros(len(data), dtype=np.int64)
    for _ in range(iterations):
        d = ((data[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
        labels = d.argmin(axis=1)
        for i in range(k):
            members = data[labels == i]
            if len(members):
                centers[i] = members.mean(axis=0)

    d = ((data[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
    labels = d.argmin(axis=1)
    counts: dict[str, int] = {}
    for i in range(k):
        n = int((labels == i).sum())
        if n == 0:
            continue
        rgb = np.clip(np.rint(centers[i]), 0, 255).astype(int)
        hex_color = "#{:02X}{:02X}{:02X}".format(*rgb)
        counts[hex_color] = counts.get(hex_color, 0) + n
    return [c for c, _ in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))]


def analyze_photos(blobs: list[bytes]) -> PhotoAnalysis:
    """Анализирует уже проверенные фото. Порядок фото сохраняется."""
    if not blobs:
        raise ValueError("нужно хотя бы одно фото")

    per_photo: list[dict[str, float]] = []
    pixel_sets: list[np.ndarray] = []
    cleaned: list[bytes] = []
    for data in blobs:
        full = load_rgb(data)
        small = downscale(full, ANALYSIS_SIZE)
        pixels = np.asarray(small, dtype=np.float64).reshape(-1, 3)
        per_photo.append(photo_stats(pixels))
        pixel_sets.append(pixels)
        cleaned.append(encode_clean_jpeg(downscale(full, STORED_MAX_SIDE)))

    def mean_of(key: str) -> float:
        return round(sum(p[key] for p in per_photo) / len(per_photo), 4)

    profile = {
        "count": len(blobs),
        "dominant_colors": kmeans_colors(np.concatenate(pixel_sets, axis=0)),
        "brightness": mean_of("brightness"),
        "contrast": mean_of("contrast"),
        "warmth": mean_of("warmth"),
    }
    return PhotoAnalysis(profile=profile, cleaned_jpegs=cleaned)
