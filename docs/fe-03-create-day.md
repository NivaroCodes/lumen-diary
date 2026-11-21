# FE-03 — Create a diary entry

The form accepts a required diary text, 1–5 JPEG, PNG or WebP photos of up to 10 MB each, and an HTTP(S) song link with a description. The text limit is 5000 characters after trimming. Optional fields include the date, song title, artist, release year, tempo, energy, genre and mode.

Photos stay in selection order and can be previewed, removed and added again. The form sends only fields accepted by [the API contract](api-contract.md). It sends one multipart request while submission is pending and opens the existing `/memory/{id}` route after HTTP 201 with an ID. Field and request errors keep the draft in the form and move focus to the field or message.

## Local verification

1. Start FastAPI using the [backend instructions](../backend/README.md). Use a temporary `DATA_DIR` for test entries.
2. In `frontend/`, run `npm ci` and `npm run dev`. Vite forwards `/api` to `http://127.0.0.1:8000`. Set `LUMEN_API_TARGET` if the API is on another port. The same proxy applies to `npm run preview`.
3. Fill the form, submit, and check for HTTP 201 and the matching ID in the destination URL. The destination shows the existing memory placeholder and the new ID.

## Acceptance

FE-03.1–FE-03.8 passed. The audits covered Chrome at 320, 390, 768 and 1440 px, keyboard navigation, validation boundaries, photo ordering, loading, draft preservation and duplicate submission. FastAPI returned 201, 400 and 500 during testing. A simulated connection failure covered the network error path.
