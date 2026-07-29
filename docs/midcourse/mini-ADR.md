# Mini-ADR: Search/Filter and Task Comments

## Status
Accepted

## Date
2026-07-29

## Context

Two new features were evaluated against the options laid out in
[`docs/architectural-decisions.md`](../architectural-decisions.md):

- **Feature 1 — Search + combined filters**: Option A (server-side filtering,
  `search`/`status`/`priority`/`assignee` handled in SQL) vs. Option B (fetch
  tasks once, filter client-side in JS). `assignee` was added to scope after
  the initial round of this decision.
- **Feature 2 — Task comments**: Option A (a normalized `Comment` SQLModel
  table with a FK to `tasks.id`) vs. Option B (comments embedded as a JSON
  blob on the `Task` row).

Both features must stay within the project's existing constraints: no
authentication, no new deployment infrastructure, SQLite + SQLModel as the
only persistence layer (per ADR-001), and no framework/build-tooling changes
to the vanilla-JS frontend.

## Decision

- **Feature 1 (search/filters): Option A** — extend `GET /tasks` with a
  `search` query param and an `assignee` query param (exact match, alongside
  the existing `status`/`priority`), all filtered server-side in
  `storage.get_all_tasks`.
- **Feature 2 (comments): Option A** — a normalized `comments` table with a
  foreign key to `tasks.id`, following the same SQLModel pattern already
  used for `Task`.

## Reasoning

**Simplicity**
- Feature 1: server-side filtering does add real moving parts — a debounce
  timer and request-cancellation/race handling that Option B didn't need.
  But with `assignee` now in scope, there are four independently combinable
  filters (`search`, `status`, `priority`, `assignee`); replicating that AND
  logic correctly in client-side JS isn't actually simpler than one more
  `.where()` predicate in `storage.get_all_tasks` — it's the same
  combinatorial logic, just duplicated in the browser instead of the
  database. Option B only looked simpler while the filter set was small.
- Feature 2: a dedicated table is *more* code up front (new model, new CRUD
  functions, new routes) than the JSON-blob option, but it is simpler in the
  sense that matters most here — each operation (add/list/delete a comment)
  maps to one obvious SQL statement, instead of a load-mutate-save dance
  over a serialized blob.

**Testability**
- Feature 1: filtering logic lives entirely in `storage.get_all_tasks` and
  can be asserted directly against the database, the same way `status`/
  `priority` filters already are in `test_storage.py`/`test_tasks.py` — one
  shared, tested code path instead of server-side status/priority filtering
  and client-side search filtering that could silently drift apart.
- Feature 2: a real table means `test_comments.py` can assert against actual
  rows (existence, count, order by `created_at`) the same way
  `test_tasks.py` already does, instead of asserting against parsed JSON
  strings pulled out of a `Task.comments_json` field.

**Local run/deploy ability**
- Neither decision changes how the app is run (`uvicorn app.main:app --reload`)
  or adds any new local dependency, service, or file beyond the existing
  `tasks.db`. Both stay inside the constraints ADR-001 already established.

**Familiarity**
- Feature 1: `status`/`priority` are already server-side, typed query params
  on `GET /tasks` in `app/main.py`. Adding `search` and `assignee` the same
  way extends that existing pattern (optional `Query` params → `.where()`
  predicates) rather than running a second, parallel filtering mechanism in
  the frontend.
- Feature 2: a SQLModel table with a `foreign_key` is the same shape as the
  existing `Task` table — same session/engine usage, same
  `SQLModel.metadata.create_all` bootstrap, no new persistence concept to
  learn.

## AI Assumptions Corrected or Rejected

1. **"Client-side filtering stays simple because the filter set stays small"
   (Feature 1, original Option B decision).** That held while the scope was
   `search` + `status` + `priority` — AND-ing three values in a JS `.filter()`
   is trivial. It stopped holding once `assignee` was added: four
   independently combinable filters is exactly the case SQL `WHERE` clauses
   exist for, and re-implementing that AND logic correctly in the browser
   (and keeping it in sync with the database on every fetch) is no longer
   the "simple" option. The debounce/request-cancellation cost of Option A
   buys correctness Option B can't offer for free at this filter count —
   corrected by moving Feature 1 to Option A once `assignee` entered scope.

2. **"Smallest diff = best option" (Feature 2, Option B).** The AI's
   write-up framed the JSON-blob approach as the "smallest possible diff"
   for comments, implicitly treating diff size as the deciding factor. That
   was rejected: the blob approach requires a read-entire-list, mutate,
   write-entire-list-back cycle for every single comment operation, has no
   database-level ordering guarantee (`ORDER BY created_at` isn't available
   inside a JSON string), and can't cleanly satisfy the 404-on-missing-comment
   behavior (US-5) without manually scanning and parsing JSON. A normalized
   table costs one extra file and a handful of CRUD functions, but that's a
   small, one-time cost against a per-request cost the blob approach pays
   forever — favoring "smallest diff today" over "correct data structure"
   was the wrong trade for this feature.

## Risks If the Project Grew

1. **SQLite's single-writer limitation.** ADR-001 already flags this, but it
   becomes more relevant once a `comments` table adds a second, likely
   higher-frequency write path (comments are typically added more often than
   tasks are created/edited). Concurrent writes to SQLite serialize at the
   database level; if this project ever supported multiple simultaneous
   users, write contention on `tasks.db` would need to be addressed —
   likely by moving to a server-based database, which ADR-001 already
   identifies as the natural next step and notes the SQLModel query API
   would carry over largely unchanged.
2. **No index on the filtered columns.** `status`, `priority`, and `assignee`
   are all plain (unindexed) columns on `tasks`; at current scale a full
   table scan per filtered `SELECT` is fine, but if task volume grew
   substantially, filtering (especially `assignee`, a free-text column with
   no small fixed set of values like the enums) would benefit from an index.
   Every filter combination is also now a network round trip — perceived
   responsiveness depends on server/DB latency, which the debounce only
   reduces, not eliminates, versus the instant feel Option B had.

## Alternatives Considered

See [`docs/architectural-decisions.md`](../architectural-decisions.md) for
the full Option A / Option B comparisons for both features, including code
sketches and folder-structure impact.

## Notes

This decision does not introduce authentication, a new database engine, or
any deployment infrastructure — those remain out of scope per the project
constraints in `CLAUDE.md` and ADR-001.
