# ADR-001: Storage Layer for Task Tracker Backend

## Status
Accepted

## Date
2026-07-03

## Context

The Task Tracker backend (Python/FastAPI/Pydantic) needs a storage layer for
tasks (`title`, `description`, `status`, `priority`, `assignee`) covering
create, validate, and list operations per US-1, US-2, and US-3.

Two lightweight architectures were evaluated:

- **Option A** — In-memory storage (Python dict/list, no persistence)
- **Option B** — SQLite + SQLModel (local file-based database)

Both options satisfy the same REST API contract, validation rules, and
response formats. The evaluation criteria were: simplicity (learning curve
and maintenance), testability with pytest/TestClient, local run/deploy
ability, and familiarity for an intermediate developer. Full comparison is
documented in the accompanying architecture comparison notes.

This is explicitly a learning project, with constraints that rule out
authentication, multi-tenancy, microservices, Docker, cloud deployment, and
production database setup.

## Decision

We will use **Option B: SQLite with SQLModel** as the storage layer.

## Reasoning

While this project is for learning purposes, the intent is for it to grow
into something usable in real-life scenarios rather than being a disposable
exercise. Given that goal, we are prioritizing a **simple path that still
leads somewhere real**, over the absolute simplest possible starting point.

Specifically:

- **Persistence matters even now.** An in-memory store loses all data on
  every restart, which doesn't match how a "real" tool needs to behave, even
  informally (e.g. across dev sessions, demos, or casual daily use).
- **SQLite + SQLModel is still lightweight.** It requires no server process,
  no Docker, and no cloud setup — just a local `.db` file — so it does not
  violate the project's simplicity constraints. It's a genuine middle ground,
  not a premature leap to production infrastructure.
- **The skills transfer.** Learning SQLModel/SQLAlchemy sessions and schema
  definition now means less relearning later if the project is extended,
  compared to the in-memory approach, which teaches a pattern (global
  mutable state) that would need to be unlearned.
- **Testability is only slightly more work.** The FastAPI dependency-override
  pattern for testing with a database is a standard, well-documented
  approach, and worth learning early rather than deferring.

## Consequences

**Positive:**
- Task data survives server restarts.
- Closer alignment with how real backend services are typically built.
- Direct skill transfer if the project later moves to Postgres/MySQL (same
  SQLModel query API).
- Establishes a schema-first mindset from the start.

**Negative / accepted trade-offs:**
- Slightly steeper learning curve: engine, session, and table metadata
  concepts are introduced immediately instead of deferred.
- A `tasks.db` file will be created locally; it needs to be gitignored and
  occasionally deleted during debugging to rule out stale state.
- No formal migration tooling (e.g. Alembic) is introduced at this stage —
  schema changes during development will be handled by deleting and
  recreating the local `.db` file, which is acceptable for a learning
  project but is explicitly **not** production-grade and would need
  revisiting if this project is ever deployed for real use.
- Test setup requires a fixture to provide a fresh database (in-memory or
  temp file) per test run, which is more boilerplate than Option A's
  reset-a-dict approach.

## Alternatives Considered

**Option A — In-memory storage** was rejected as the primary approach. It
remains the simpler option for pure API/validation-focused learning, but
was not chosen because it does not support the goal of the project
evolving into something usable beyond a single running session, and it
does not build persistence-related skills.

## Notes

This decision does not introduce authentication, multi-tenancy,
microservices, Docker, or cloud deployment — those remain explicitly out of
scope per the project constraints and would be the subject of future ADRs
if and when the project's goals expand further.
