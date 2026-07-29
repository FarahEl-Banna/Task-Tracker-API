# AI Prompt Log

This log documents the prompts used to design and implement two features on top of the Module 1 Task Tracker: **Search + combined filters** and **Task comments**. For each feature it includes at least three meaningful prompts, a summary of what the AI returned, and what was accepted, edited, or rejected. One weak prompt is shown alongside a stronger rewrite (Feature 1, Prompt 2).

---

## Feature 1: Search + Combined Filters

### Prompt 1 — Technical decisions before coding

> I built a Task Tracker REST API using Python and FastAPI. The app supports create, view, update, and delete tasks. Each task has id, title, description, status (ToDo, InProgress, Done), priority (Low, Medium, High). Module 1 scope excludes authentication, user accounts, multi-tenancy, real-time updates, mobile app, notifications, production database, and deployment.
>
> I am adding a feature Search + combined filters: Extend GET /tasks to support text search and combinations such as status, priority.
>
> List the five most important technical decisions I should make before writing any code. For each decision, explain why it matters and suggest a default choice for a small learning project. Constraints: - Do not assume authentication, Docker, cloud deployment, real-time updates, or a complex frontend. - Keep recommendations appropriate, where the goal is a simple learning to add features in an existing project. Output format: Return a table with columns: Decision, Why it matters, Suggested default, Assumption to verify.

**AI output:** A decision table (raw response not saved to this log — a gap noted for future prompts). Based on the follow-up in Prompt 2, it included a suggested set of query parameter names for search/filter.

**Accepted / edited / rejected:** Rejected the AI's assumed query parameter names (`q`, `status`, `priority`) once checked against the actual model — this is what Prompt 2 corrects.

---

### Prompt 2 — Correcting a bad assumption *(weak prompt → rewritten stronger version)*

**Original prompt (as sent — weak):**

> you assumed q, status, priority as the param names. the model uses the field names: title: str description: str = "" status: str = TaskStatus.TODO.value priority: str = TaskPriority.MEDIUM.value assignee: Optional[str] = None use this to create the url where we can filter by status or priority and search description and title. edit the user story 1

**Why it's weak:** No greeting/role framing, no explicit deliverable format, run-on sentence mixing correction + instruction + task, and "edit the user story 1" assumes the AI remembers which story that is without restating it.

**Rewritten (stronger) version:**

> The previous response assumed query parameter names `q`, `status`, and `priority` that don't match this codebase. The actual `Task` model fields are: `title: str`, `description: str`, `status: str` (enum `TaskStatus`), `priority: str` (enum `TaskPriority`), `assignee: Optional[str]`.
>
> Task: Using these exact field names, define the query parameters for `GET /tasks` that support (a) free-text search across `title` and `description`, and (b) exact-match filtering on `status`, `priority`, and `assignee`, combinable with AND logic.
>
> Then revise "User Story 1" (the live-search-with-filters story) so its acceptance criteria reference these corrected parameter names instead of the placeholder ones.
>
> Output format: 1) a short table of param name → maps to which field(s) → match type (exact vs substring), 2) the revised User Story 1 with acceptance criteria.

**AI output:** A corrected user story (surfaced later as the "User Story 1 (draft)" block quoted in Prompt 3) using `status`, `priority`, and a search parameter matching the real model fields.

**Accepted / edited / rejected:** Accepted the corrected field-name mapping; carried the revised User Story 1 forward as context into Prompt 3.

---

### Prompt 3 — Architecture options + debounce design

> You are a senior backend developer helping me evaluate lightweight architectures for a learning to add a feature in an existing project. Context: I am building a Task Tracker application with a Python/FastAPI backend and a simple web frontend. Reviewed requirements: User Story 1 (draft): [live search + status/priority filters, AND logic, empty-list-not-error, debounce requirement]
>
> The overload problem, and the fix: debouncing — [explanation of why firing a request per keystroke is wasteful, and the standard debounce fix]
>
> Constraints: learning project, FastAPI + Pydantic, SQLite + SQLModel, no auth/multi-tenancy, no microservices/Docker/cloud/production DB. Task: Propose two different lightweight architectures. For each option, provide: 1. Tech stack and data storage edits needed 2. Folder structure edits 3. Data model sketch with Pydantic fields and constraints 4. Three trade-offs compared to the other option. Output format: Option A and Option B in clearly separated sections. Do not choose for me.

**AI output:** Two architecture options — Option A (backend-driven filtering: query params hit the database per request) and Option B (single fetch, filter/search client-side in the frontend).

**Accepted / edited / rejected:** Accepted **Option B** — one fetch, search/filter done in the frontend — for simplicity and to reduce API calls (recorded in `docs/adr/mini-ADR.md`). Rejected Option A for this feature.

---

## Feature 2: Task Comments

### Prompt 1 — User stories

> You are a product owner writing user stories for a small development team. Context: [Task Tracker feature set]. I need to add a new feature: Task comments. Add comment model or task comment list. Support list/add/delete comment behavior with non-blank text validation and not-found handling. Explicitly out of scope: authentication, user accounts, multi-tenancy, real-time updates, mobile app, notifications, production database/deployment. Target user: A solo developer or small team managing work in a single shared task list. Task: Generate 3-5 user stories in the format: As a [role], I want [feature] so that [benefit]. Constraints: - Use "team member" as the main role. - 2-3 acceptance criteria per story, specific and testable. - Cover happy paths and at least one failure case. Output format: table with columns ID, Story, Acceptance Criteria, Notes / Assumptions.

**AI output:** Six user stories (US-1 through US-6) covering add/list/delete comments, blank-text rejection (400), not-found handling (404), and a 1000-character limit (`MAX_COMMENT_LENGTH`), each with concrete acceptance criteria and an assumptions column (e.g., no author field, ordering to be confirmed).

**Accepted / edited / rejected:** Accepted all six stories as-is and carried the full table forward as context into the next prompt.

---

### Prompt 2 — Architecture options for comment storage

> [Same senior-backend-developer framing as Feature 1 Prompt 3, with the six comment user stories as context.] Constraints: learning project, FastAPI + Pydantic, SQLite + SQLModel, no auth/multi-tenancy, no microservices/Docker/cloud/production DB. Task: Propose two different lightweight architectures for storing/serving comments. Output format: Option A and Option B in clearly separated sections. Do not choose for me.

**AI output:** Option A (a normalized `comments` SQL table, FK to `tasks`) vs. Option B (comments embedded/serialized on the task row, e.g. as JSON).

**Accepted / edited / rejected:** Accepted **Option A** — a dedicated SQL table for comments — for better business-logic support, easier CRUD/search, and a cleaner data structure (recorded in `docs/adr/mini-ADR.md`). Rejected Option B.

---

### Prompt 3 — Generate the ADR

> [with `@docs/architectural-decisions.md` attached] Based on the .md file the decisions I took are: feature 1: option B, one fetch and search in the frontend for simplicity and reduction of api calls; feature 2: option A, creating a sql table for comments — best for business logic, easier CRUD/search operations, and a better data structure. Task: create my ADR in `doc/adr/mini-ADR.md`, including: - the chosen architecture and storage approach - why I chose it using simplicity, testability, local run/deploy ability, and familiarity - at least two AI assumptions I corrected or rejected - one or two risks I would address if the project grew.

**AI output:** A draft ADR at `docs/adr/mini-ADR.md` documenting both architecture choices and rationale.

**Accepted / edited / rejected:** Edited after generation — the project needed a **backend function** for both features (not just a frontend/storage description), so the ADR was updated accordingly once that gap was noticed.

---

### Prompt 4 — Review the ADR against the grading criteria

> [with `@docs/adr/mini-ADR.md` attached] Now rewrite the ADR to implement decision B for feature 1 (Search/Filter) and Task Comments, extending GET /tasks to support text search and combinations such as status, priority, assignee. Task: Check whether my ADR includes: - the chosen architecture and storage approach - why I chose it using simplicity, testability, local run/deploy ability, and familiarity - at least two AI assumptions I corrected or rejected - one or two risks I would address if the project grew. Constraints: - Do not generate a replacement ADR. - Do not polish the prose for me. - Give only review feedback and minimal suggestions.

**AI output:** Review-only feedback against the four required ADR elements (not preserved verbatim in this log — worth appending next time this prompt pattern is reused).

**Accepted / edited / rejected:** Used as a checklist pass rather than a rewrite, per the explicit constraint not to have the AI regenerate the document.

---

### Prompt 5 — Backend implementation plan (no code)

> You are a senior Python backend engineer. Generate TWO files for a FastAPI Task Tracker REST API. Context: [existing endpoint table, SQLite]. I need to implement Task comments — add comment model or task comment list, support list/add/delete with non-blank text validation and not-found handling. [US-2, US-3, US-4, US-6 quoted in full] Based on `@docs/architectural-decisions.md` I need a proposed plan to work on to implement this feature, starting with the backend, changes must be in `@app/main.py`, `@app/models.py`, `@app/storage.py`, propose if a file is needed to be added, and `@tests/test_tasks.py` for testing. Do not write any code, only what functions and files are needed.

**AI output:** A file-by-file plan: `Comment`/`CommentCreate`/`CommentResponse` in `models.py`; `MAX_COMMENT_LENGTH` and `validate_comment_text()` in `business_rules.py`; `add_comment`/`get_comments_for_task`/`delete_comment` in `storage.py`; three new routes in `main.py`; a new `tests/test_comments.py` (not mixed into `test_tasks.py`) with ten proposed test cases. It flagged one open decision: whether blank/over-length comment text should return `400` (as literally stated in US-4/US-6) via an explicit `HTTPException`, or `422` via a Pydantic `field_validator` (consistent with how `Task` fields are already validated).

**Accepted / edited / rejected:** Accepted the plan's file layout and the separate `tests/test_comments.py` file, both implemented as proposed. On the flagged 400-vs-422 decision, the implementation went with **422 via a Pydantic `field_validator`** (`app/models.py` `CommentCreate.validate_text` calling `validate_comment_text`) — prioritizing consistency with existing `Task` validation over the literal `400` wording in the user stories.

---

### Prompt 6 — Frontend implementation plan (incremental steps)

> Before writing code, give me an incremental plan for building this feature in small Copilot/Codex loops. Feature: Task comments — list/add/delete with non-blank text validation and not-found handling. Add a comments section in the edit modal or a small task detail area. Show comment count on cards if useful. Add comment, reject blank comment, list comments for a task, delete comment, 404 for missing task/comment. Output format: table with columns Step, File or selection, What changes, How I verify it.

**AI output:** An 8-step table: steps 0–6 cover the core comments UI in `frontend/index.html` (modal markup, fetch helpers, rendering the list, add/delete handlers, clearing state on modal close); steps 7–8 were marked **optional/stretch** and explicitly flagged as a backend schema change (`comment_count` on `TaskResponse`) requiring confirmation first, per CLAUDE.md's do-not-rules around schema/UI changes.

**Accepted / edited / rejected:** Accepted steps 0–6 as the core UI build (`#comment-list`, `#comment-text-input`, `.comment-list` styling now in `frontend/index.html`). **Accepted step 7** — `comment_count` was added to `TaskResponse` and is computed in `app/storage.py` (`_comment_count_for_task`, `_comment_counts_by_task_id`). **Rejected/deferred step 8** — no card-level comment-count badge exists in `frontend/index.html`; the count is available from the API but not yet surfaced in the UI.
