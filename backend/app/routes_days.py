"""Эндпоинты дней и выдача фото (BE-07)."""
from __future__ import annotations

import hashlib

from fastapi import APIRouter, Query, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from starlette.datastructures import UploadFile

from .errors import ApiError, validation_error
from .music import build_music_profile, build_music_record
from .photo_analysis import analyze_photos
from .schemas import DayInput, DayRecord, DaySummary
from .storage import NewDay, Storage
from .text_analysis import analyze_text, make_title
from .validation import PhotoBlob, read_photo, validate_day_form
from .visual_model import build_visual, compute_seed

router = APIRouter(tags=["days"])
media_router = APIRouter(tags=["media"])

_CREATE_OPENAPI = {
    "requestBody": {
        "required": True,
        "content": {
            "multipart/form-data": {
                "schema": {
                    "type": "object",
                    "required": ["text", "photos", "music_url", "music_description"],
                    "properties": {
                        "text": {"type": "string", "minLength": 1, "maxLength": 5000},
                        "photos": {"type": "array", "minItems": 1, "maxItems": 5,
                                   "items": {"type": "string", "format": "binary"},
                                   "description": "JPEG, PNG или WebP. Поле также принимается как photos[]."},
                        "music_url": {"type": "string", "maxLength": 500},
                        "music_description": {"type": "string", "minLength": 1, "maxLength": 300},
                        "music_title": {"type": "string", "maxLength": 200},
                        "music_artist": {"type": "string", "maxLength": 200},
                        "music_year": {"type": "integer", "minimum": 1900},
                        "music_genre": {"type": "string", "maxLength": 40},
                        "music_tempo_bpm": {"type": "number", "minimum": 40, "maximum": 220},
                        "music_energy": {"type": "number", "minimum": 0, "maximum": 1},
                        "music_mode": {"type": "string", "enum": ["major", "minor", "unknown"]},
                        "weather": {"type": "string", "enum": ["rain", "fog", "cloud", "sun"],
                                    "description": "Необязательно. Погода, выбранная вручную; важнее погоды из текста."},
                        "place": {"type": "string", "maxLength": 80,
                                  "description": "Необязательно. Место, введённое вручную."},
                        "date": {"type": "string", "format": "date",
                                 "description": "Необязательно, YYYY-MM-DD. По умолчанию сегодня."},
                    },
                }
            }
        },
    }
}


def _storage(request: Request) -> Storage:
    return request.app.state.storage


def _process_day(day_input: DayInput, photos: list[PhotoBlob]) -> NewDay:
    """Тяжёлая часть (Pillow, numpy): анализ входов и расчёт VisualModel."""
    photo_hashes = [hashlib.sha256(p.data).hexdigest() for p in photos]
    analysis = analyze_photos([p.data for p in photos])
    music_profile = build_music_profile(day_input.music)
    profile = {
        "text": analyze_text(day_input.text),
        "photos": analysis.profile,
        "music": music_profile,
        "context": {
            "weather": day_input.weather,
            "weather_source": "chosen" if day_input.weather else "text",
            "place": day_input.place,
        },
    }
    # Погода, выбранная вручную, важнее погоды из текста — и для названия, и для сцены.
    title_profile = {**profile["text"], "weather": day_input.weather} if day_input.weather else profile["text"]
    title = make_title(title_profile)
    seed = compute_seed(day_input.text, photo_hashes, day_input.music.url, day_input.music.description)
    visual, explain = build_visual(profile, seed, title)
    return NewDay(
        date=day_input.date,
        title=title,
        text=day_input.text,
        music=build_music_record(day_input.music, music_profile),
        profile=profile,
        visual=visual,
        explain=explain,
        photos=analysis.cleaned_jpegs,
    )


@router.post("/days", status_code=201, response_model=DayRecord, openapi_extra=_CREATE_OPENAPI,
             summary="Создать день")
async def create_day(request: Request) -> dict:
    settings = request.app.state.settings
    form = await request.form()
    uploads = [v for key in ("photos", "photos[]") for v in form.getlist(key)]
    blobs: list[PhotoBlob] = []
    for upload in uploads:
        if isinstance(upload, UploadFile):
            blobs.append(await read_photo(upload, settings.max_upload_bytes))
        else:  # строка вместо файла
            blobs.append(PhotoBlob(filename="", content_type="text/plain", data=b""))

    def work() -> str:
        day_input = validate_day_form(form, blobs, settings)
        return _storage(request).create_day(_process_day(day_input, blobs))

    day_id = await run_in_threadpool(work)
    return _storage(request).get_day(day_id)


@router.get("/days", response_model=list[DaySummary], summary="Архив дней")
def list_days(request: Request, sort: str = Query("date_desc")) -> list[dict]:
    if sort != "date_desc":
        raise validation_error("sort", "Поддерживается только sort=date_desc")
    return _storage(request).list_days()


@router.get("/days/{day_id}", response_model=DayRecord, summary="Один день")
def get_day(day_id: str, request: Request) -> dict:
    day = _storage(request).get_day(day_id)
    if day is None:
        raise ApiError(404, "not_found")
    return day


@media_router.get(
    "/media/{day_id}/{filename}",
    summary="Фото дня",
    response_class=FileResponse,
    responses={
        200: {
            "description": "Очищенное фото дня (JPEG без EXIF)",
            "content": {"image/jpeg": {"schema": {"type": "string", "format": "binary"}}},
        },
        404: {
            "description": "Фото не найдено",
            "content": {"application/json": {"example": {"error": "not_found"}}},
        },
    },
)
def get_media(day_id: str, filename: str, request: Request) -> FileResponse:
    path = _storage(request).photo_path(day_id, filename)
    if path is None:
        raise ApiError(404, "not_found")
    return FileResponse(path, media_type="image/jpeg")
