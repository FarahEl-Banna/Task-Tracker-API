# 1st feature: Search + combined filters

## Decision table

| Decision | Why it matters | Suggested default | Assumption to verify |
|---|---|---|---|
| Query parameter contract — how search text and filters are expressed in the URL | This defines the actual shape of your API and how easy it is to extend later (sorting, pagination). Getting it right up front avoids breaking changes. | `GET /tasks?q=<text>&status=<enum>&priority=<enum>&assignee=<text>`, all optional, added as separate query params rather than one combined "filter" blob | That search only needs to match title/description, not id or other fields |
| Where filtering executes — database query vs. in-memory Python filtering | Determines code complexity and performance. If your storage is a Python list/dict, filtering in Python is simplest; if it's SQLite/SQLAlchemy, doing it in the query (WHERE) is simpler and more correct than fetching everything first. | Decision: Option A from `architectural-decisions.md` — filter in the SQLAlchemy query (`.where()`) in `storage.get_all_tasks`, not in-memory Python. | What your current persistence layer actually is — this decision depends entirely on it |
| Combination logic — AND vs. OR when multiple filters + search are given together | "Search + combined filters" is ambiguous until you define this. It changes both the implementation and what a "correct" test result looks like. | AND semantics: all provided conditions must match (intersection), e.g. `status=Done&priority=High&assignee=Sam` returns tasks matching all three | That you don't also need OR-style multi-select (e.g., `status=ToDo,Done`) — that would need a different param format |
| Search matching strategy — which fields, case sensitivity, partial vs. exact | Defines what "search" actually means to a user and how complex the implementation gets. A learning project doesn't need full-text search infrastructure. | Case-insensitive substring match on title and description (`LOWER(field) LIKE '%text%'` in SQL, or `text.lower() in field.lower()` in memory) | Whether search should include description or just title |
| Input validation & empty/invalid handling | Determines robustness: what happens with a bad status value, an empty `q`, or zero matches. Prevents silent bugs or unhandled 500s. | Reuse your existing status/priority Enums as the query param types so FastAPI auto-validates and returns 422 on bad input; `assignee` is a plain string (matches `Task.assignee`'s type, no enum) so any value is accepted — an unmatched assignee just yields no results, not a 422; missing params = no filter applied; no matches = 200 OK with an empty list (not 404) | Confirmed: `TaskStatus`/`TaskPriority` are already Enums (`app/models.py`), and `GET /tasks` already accepts them as typed query params (`app/main.py`) — reuse as-is, no new validation to write. `assignee` is `Optional[str]` on `Task`, not an enum, so it needs no new validation either. |

## Use case fixed

### User Story 1 (draft)

As a user of the Task Tracker, I want the task list to update automatically as I type in the search box — combined with any active status/priority/assignee filters — so that I can see relevant results in real time without submitting a search manually.

### Acceptance criteria (draft)

- As the user types in the search field, the task list re-filters live, without a page reload or a submit button
- `GET /tasks?status=<value>` returns tasks matching that status exactly
- `GET /tasks?priority=<value>` returns tasks matching that priority exactly
- `GET /tasks?assignee=<value>` returns tasks matching that assignee exactly (exact string match, case-sensitive, same as how `assignee` is stored)
- An invalid `status` or `priority` value (not one of the defined `TaskStatus`/`TaskPriority` enum values) returns 422 Unprocessable Entity, via FastAPI's existing enum validation — no new validation logic needed
- An `assignee` value that matches no task is not an error — it returns 200 OK with an empty list, since `assignee` is a free-text field, not an enum, so there's no invalid-value case to reject
- Any combination of search, status, priority, assignee narrows results using AND logic
- No matches returns 200 OK with an empty list, not an error
- Omitting all params returns the full task list (current behavior unchanged)
- The UI does not send an API request on every single keystroke (see implementation note below)

### The overload problem, and the fix: debouncing

If you fire `GET /tasks?search=...` on every keystroke, typing "login" alone sends 5 requests, most of which return before the user has finished typing and are immediately discarded. This wastes backend load and can cause race conditions where an older, slower response overwrites a newer one.

Standard fix: debounce the input. Wait until the user pauses typing for a short interval before firing the request, resetting the timer on every keystroke.

| Decision | Suggested default | Why |
|---|---|---|
| Debounce delay | 300–400ms | Long enough to skip most in-progress typing, short enough to still feel instant |
| Minimum characters before searching | 2 characters | Avoids firing a broad, expensive query on a single keystroke |
| Stale response handling | Track a request ID/timestamp; ignore any response that isn't from the latest request | Prevents an old slow response from overwriting newer results (race condition) |
| Trigger on filter changes (status/priority/assignee) | No debounce needed — fire immediately | These are discrete dropdown/click events, not continuous typing, so there's no flood risk |

---

# 2nd feature: Task comments

Architected comprehensive user stories covering comment creation, retrieval, deletion, and validation
Architected comprehensive user stories covering comment creation, retrieval, deletion, and validation

| ID | Story | Acceptance Criteria | Notes / Assumptions |
|---|---|---|---|
| US-1 | As a team member, I want to add a comment to a task so that I can record notes or updates for others to see. | 1. Given a valid task ID and non-blank comment text, when I submit the comment, it is saved and linked to that task.<br>2. The created comment is returned with a unique ID and a timestamp.<br>3. Comment text is stored exactly as submitted (no formatting/markdown processing). | Assumes a comment has at minimum: id, task_id, text, created_at. No author field, since there are no user accounts. |
| US-2 | As a team member, I want to view the list of comments on a task so that I can review the history and context of that task. | 1. Given a task with existing comments, requesting its comment list returns all comments ordered by creation time.<br>2. Given a task with no comments, the list request returns an empty list, not an error.<br>3. Each comment in the list includes its text and created timestamp. | Assumes chronological order = oldest first, ascending; confirm with team before implementation. |
| US-3 | As a team member, I want to delete a comment so that I can remove outdated or incorrect information. | 1. Given an existing comment ID, deleting it removes it from the task's comment list.<br>2. Deleting a comment does not affect the parent task or any other comments.<br>3. A successful delete returns a confirmation response (e.g., 204 No Content). | No edit/update capability included, since it wasn't in scope — only add/list/delete. |
| US-4 | As a team member, I want to be blocked from submitting a blank comment so that the task's comment history stays meaningful and clutter-free. | 1. Given comment text that is empty or whitespace-only, submitting it is rejected with a 400 error.<br>2. The error response includes a message indicating the text cannot be blank.<br>3. No comment record is created, and the task's existing comment list is unchanged. | Failure case covering input validation. |
| US-5 | As a team member, I want a clear error when I try to add, view, or delete comments for a task or comment that doesn't exist, so that I understand why the action failed. | 1. Given a non-existent task ID, adding or listing comments returns a 404 error with a descriptive message.<br>2. Given a non-existent comment ID, deleting it returns a 404 error with a descriptive message.<br>3. No partial data is created or removed as a result of the failed request. | Failure case covering not-found handling across all three comment operations. |

P-- set a use case where there is a limit on the length of the comment to a 1000 and enforce it in both the back and frontend

| ID | Story | Acceptance Criteria | Notes / Assumptions |
|---|---|---|---|
| US-6 | As a team member, I want to be blocked from submitting a comment longer than 1000 characters so that the task's comment history stays readable and the system stays performant. | 1. Backend: Given comment text longer than 1000 characters, the API rejects the request with a 400 error and a message stating the 1000-character limit. Text of exactly 1000 characters is accepted; 1001 characters is rejected.<br>2. Frontend: The comment input shows a live character counter (e.g., "842/1000") and prevents typing or submitting beyond 1000 characters, giving the user feedback before a request is sent.<br>3. Consistency: If the frontend limit is ever bypassed (e.g., direct API call), the backend still enforces the 1000-character cap independently — backend validation is the source of truth, frontend is a UX convenience. | 1000 is now the fixed limit, not a placeholder — implement as a named constant/config (e.g., MAX_COMMENT_LENGTH = 1000) shared or duplicated consistently between frontend and backend so it's easy to adjust later. |
