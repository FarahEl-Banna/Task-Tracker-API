# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Module 4 Task Tracker: a Task Tracker REST API (FastAPI + SQLModel/SQLite) with a vanilla-JS kanban frontend. The README still describes an earlier "Module 1" milestone (health check only, no CRUD, no frontend); the code has since grown well past that — treat `app/main.py`, `app/models.py`, `app/business_rules.py`, and the tests as the source of truth over the README. See `docs/adr/001-storage-layer.md` for why SQLite+SQLModel was chosen.

## 1. Tech Stack

- **Python** — [VERIFY]: local `venv/pyvenv.cfg` reports 3.13.14 and `README.md` says "3.10+"; if this course targets 3.11 specifically, confirm which is authoritative before relying on version-specific behavior.
- **FastAPI** 0.139.0 (`requirements.txt`)
- **Pydantic v2** 2.13.4 (`requirements.txt`)
- **Uvicorn** 0.50.2 (`requirements.txt`)
- **pytest** 9.1.1 (`requirements.txt`)
- **httpx** 0.28.1 — not pinned directly in `requirements.txt`, but present in `requirements.lock.txt` as a transitive dependency; it backs FastAPI's `TestClient` used throughout `tests/`.
- **Frontend**: vanilla JavaScript, no framework/build step — single file at `frontend/index.html`.
- Also present (not in the course's core list above, but real and load-bearing): **SQLModel** 0.0.39 + **SQLAlchemy** 2.0.51 over **SQLite** for persistence, and **python-dotenv** 1.2.2 for `.env` loading.

## 2. Run Command

```bash
uvicorn app.main:app --reload --port 8000
```

## 3. Test Command

```bash
pytest -v
```

## 4. Architecture Summary

- **Backend** (`app/`):
  - `main.py` — FastAPI app instance, CORS middleware, and all route handlers (`/health`, `/tasks` CRUD). Handlers do request/response wiring and 404 checks, delegating persistence to `storage.py` and status-transition validation to `business_rules.py`.
  - `models.py` — `TaskStatus`/`TaskPriority` enums; `Task` (SQLModel table); `TaskCreate`/`TaskUpdate` (Pydantic input schemas, `extra="forbid"`, shared title validation); `TaskResponse` (output schema, `id` serialized as `str`).
  - `storage.py` — all DB access (SQLite via a cached SQLModel engine); accepts an optional `engine=` for test isolation.
  - `config.py` — loads `PORT`/`APP_ENV` from `.env`.
  - `routers/` — currently just an empty placeholder package.
- **Frontend**: `frontend/index.html` — single static file (HTML/CSS/JS inline), no build step. Talks to the API via `fetch` against a hardcoded `API_BASE`.
- **Tests** (`tests/`): `test_health.py`, `test_tasks.py` (API-level, via `TestClient`), `test_storage.py` (storage-layer, own tmp-path engine), `conftest.py` (shared fixtures), `verify_a.py` (standalone script, not a pytest module).
- **Task rules live in `app/business_rules.py`** — the single source of truth for status-transition validation, enforced from `main.py`'s PATCH handler.

## 5. Business Rules

Verified directly against `app/models.py` and `app/business_rules.py`:

- **Status values** (`TaskStatus`): `ToDo`, `InProgress`, `Done`.
- **Priority values** (`TaskPriority`): `Low`, `Medium`, `High`. No transition restrictions apply to priority — `business_rules.py` only defines a status state machine.
- **Status transition rules** (`VALID_TRANSITIONS` in `business_rules.py`), enforced only on `PATCH /tasks/{id}` and only when `status` is present in the request body:
  - `ToDo -> InProgress`
  - `InProgress -> Done`
  - `Done -> InProgress`
  - Same-status no-ops are explicitly allowed: `ToDo -> ToDo`, `InProgress -> InProgress`, `Done -> Done`
  - Any other transition (e.g. `ToDo -> Done` directly, or `Done -> ToDo`) is rejected with `422 Unprocessable Entity` and a detail message listing the allowed transitions.
- **Title validation** (`TaskCreate`/`TaskUpdate` field validator): trimmed, must be non-empty after trimming, max 200 characters. Missing/blank/oversized titles are rejected with `422`.
- **Unknown fields** are rejected with `422` (`model_config = ConfigDict(extra="forbid")` on both `TaskCreate` and `TaskUpdate`).
- **PATCH is a partial update**: only fields explicitly present in the request body are changed (`exclude_unset=True`).

## 6. UI States and CORS Notes

- **UI states** (`frontend/index.html`, `boardState` variable): `'loading'`, `'ready'`, `'error'` — drives whether the loading skeleton, the loaded kanban board, or the error card (`"Unable to load tasks right now."`) is rendered. Each board column also has its own empty state (`"Drop task here"`) when it has no cards.
- **Modal states**: `modalMode` is `'create'` or `'edit'`, controlling whether the task modal POSTs to `/tasks` or PATCHes `/tasks/{id}`.
- **CORS** (`app/main.py`): `allow_origins` is an explicit allowlist — `http://localhostt:5500` (note: this looks like a typo for `localhost`, but it's what's literally in the code — [VERIFY] with whoever owns this file before "fixing" it), `http://127.0.0.1:5500`, `http://localhost:5173`, and `"null"` (permits `file://`-origin requests in some browsers). `allow_methods` and `allow_headers` are both `"*"`; `allow_credentials` is `False`. The frontend's `API_BASE` (`http://localhost:8000`, `frontend/index.html:476`) must stay in sync with wherever the frontend is actually served from, or requests will be blocked by CORS.

## 7. Do-Not Rules

Without asking first, do not:

- Add authentication / user accounts.
- Add or change the database (e.g. swap SQLite for another engine, add migrations, change the persistence approach beyond what ADR-001 already describes).
- Add deployment steps (Docker, cloud hosting, CI/CD).
- Make major UI changes to `frontend/index.html` (new views, layout overhauls, new frameworks/build tooling).

These match the project's explicit out-of-scope list (see `README.md`'s "What's Intentionally Not Here Yet" and `docs/adr/001-storage-layer.md`).
