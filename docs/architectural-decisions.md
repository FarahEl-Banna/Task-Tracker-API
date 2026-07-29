# 1st feature: Search + combined filters

## Option A — Server-side filtering (search joins status/priority/assignee as query params)

### 1. Tech stack / storage edits

No new dependencies. Extend the existing SQLAlchemy where() chain in storage.get_all_tasks with two more optional predicates:

```python
def get_all_tasks(status=None, priority=None, assignee: str | None = None, search: str | None = None) -> list[TaskResponse]:
    ...
    if assignee:
        statement = statement.where(Task.assignee == assignee)
    if search:
        statement = statement.where(col(Task.title).contains(search))
```

main.py's list_tasks route gains matching assignee: str | None = None and search: str | None = None params, passed straight through — same shape as the existing status/priority params, no new abstraction. assignee is an exact match (like status/priority), not folded into the free-text search.

### 2. Folder structure edits

None. Changes live entirely inside app/main.py and app/storage.py. Optionally add tests/test_tasks_search.py following the existing test_tasks.py pattern.

### 3. Data model sketch

No new Pydantic model needed — matches the existing style where list_tasks(status: TaskStatus | None, priority: TaskPriority | None) takes plain optional params rather than a wrapper. If you wanted one anyway:

```python
class TaskFilters(BaseModel):
    search: str | None = Field(default=None, max_length=200)
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    assignee: str | None = None
```

(Not recommended here — it'd be inconsistent with how status/priority are already declared as bare Query params.)

Frontend: add a search `<input>` plus status/priority/assignee filters (selects for the enums, a text input for assignee) to the board toolbar. On input, debounce 300–400ms and refetch GET /tasks?search=...&status=...&priority=...&assignee=...; on filter change (status/priority/assignee), refetch immediately with the current search text merged in. Track requests with an AbortController (or a monotonic request id) so a slow, stale response can't overwrite a newer one — debouncing alone reduces races, it doesn't eliminate them.

### 4. Trade-offs vs. Option B

- Scales correctly if the task list grows large (filtering happens in SQL, not shipped to the browser) — but for this project's likely task volume, that scalability isn't a real need yet.
- Adds real moving parts: a debounce timer and request-cancellation/race handling per keystroke, versus none in Option B.
- Every filter combination is a network round trip, so perceived responsiveness depends on server latency (fine locally, but it's one more thing that can degrade or error mid-typing).

## Option B — Fetch once, filter client-side (extends the pattern already in the code)

### 1. Tech stack / storage edits

None on the backend — status/priority query params already exist and are untouched. No search param is added to the API at all.

### 2. Folder structure edits

None — everything is inside frontend/index.html's existing script block, next to the current tasks array and render function.

### 3. Data model sketch

No backend model changes. Client-side, just a plain JS filter state object (no Pydantic involved, since it never crosses the wire):

```javascript
let filterState = { search: '', status: '', priority: '' };

function applyFilters(tasks) {
  return tasks.filter(t =>
    (!filterState.status   || t.status === filterState.status) &&
    (!filterState.priority || t.priority === filterState.priority) &&
    (!filterState.search   || t.title.toLowerCase().includes(filterState.search.toLowerCase()))
  );
}
```

Call applyFilters(tasks) at the top of the existing render function (line ~583) instead of the raw tasks array.

### 4. Trade-offs vs. Option A

- Directly reuses the existing pattern (fetch all once, filter in JS for columns) — smallest, lowest-risk diff, and stays maximally simple per the project's constraints.
- Search feels instant (no network round trip) and trivially satisfies "no request per keystroke" — there's no debounce/cancellation logic to get wrong, since there's nothing to cancel.
- The in-memory list can go stale between fetches (another tab's edit, or a task added elsewhere) until the next full reload — a staleness window Option A doesn't have, since every keystroke re-queries the source of truth. Also doesn't scale if the task table grows large enough that shipping the whole list becomes wasteful.
- Both options add a small search/filter toolbar to the board UI (not currently present) — worth flagging against the "no major UI changes" rule in CLAUDE.md, though a toolbar addition (not a new view or layout overhaul) reads as in-bounds to me; confirm if you'd rather treat that as needing sign-off too.

---

# 2nd feature: Task comments

## Option A — Normalized: separate Comment table (FK to tasks.id)

### 1. Tech stack / storage edits

- No new dependencies. Same FastAPI + SQLModel + SQLite stack.
- New SQLModel table comments with a foreign key to tasks.id, created the same way Task is (SQLModel.metadata.create_all in init_db).
- MAX_COMMENT_LENGTH = 1000 added as a constant in app/business_rules.py (it already owns the one existing business rule, status transitions — natural home for a second small rule), and mirrored as a JS constant in frontend/index.html.

### 2. Folder structure edits

```
app/
├── models.py          # add Comment, CommentCreate, CommentResponse
├── storage.py          # add comment CRUD functions (or split into storage_comments.py)
├── business_rules.py   # add MAX_COMMENT_LENGTH + blank/length validation helper
├── main.py              # add routes below
tests/
├── test_comments.py     # new, mirrors test_tasks.py
```

Routes added to main.py (or, if you want to start actually using the empty routers/ package, a new app/routers/comments.py included via app.include_router):

- POST /tasks/{task_id}/comments
- GET /tasks/{task_id}/comments
- DELETE /comments/{comment_id}

### 3. Data model sketch

```python
class Comment(SQLModel, table=True):
    __tablename__ = "comments"
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="tasks.id", index=True)
    text: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CommentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str

    @field_validator("text", mode="before")
    @classmethod
    def validate_text(cls, value: object) -> str:
        if not isinstance(value, str):
            raise TypeError("text must be a string")
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("comment text cannot be blank")
        if len(value) > MAX_COMMENT_LENGTH:
            raise ValueError(f"comment text must be {MAX_COMMENT_LENGTH} characters or fewer")
        return value  # store as submitted, not the stripped version (US-1.3)

class CommentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    task_id: str
    text: str
    created_at: datetime
```

Note: US-1.3 says "stored exactly as submitted," so the validator should reject on blank/length but return the original value, not cleaned, matching the existing TaskCreate pattern only loosely (that one does store the trimmed title — here you'd deliberately diverge).

### 4. Trade-offs vs. Option B

- ✅ Comments are independently queryable/indexable (WHERE task_id = ?), which matters if you ever add pagination, sorting, or search over comments.
- ✅ Deleting one comment is an isolated DELETE ... WHERE id = ? — no read-modify-write race, no risk of corrupting other comments (directly satisfies US-3.2 "cleanly").
- ❌ More surface area for a learning project: a new table, a new set of CRUD functions, a migration-shaped change to the schema (though create_all handles it for free since there's no migration tooling yet).

## Option B — Embedded: comments as a JSON list on the Task row

### 1. Tech stack / storage edits

- No new dependencies, no new table. Add one column to Task: comments_json: str = "[]" (a serialized JSON array of {id, text, created_at} objects), read/written with json.loads/json.dumps inside storage.py.
- MAX_COMMENT_LENGTH constant lives in the same place as Option A.
- Comment IDs are generated in-process (e.g. max(existing_ids) + 1, or uuid4().hex to avoid collision bookkeeping) since there's no autoincrement PK backing them.

### 2. Folder structure edits

```
app/
├── models.py          # add CommentItem (plain BaseModel, not a table), CommentCreate, CommentResponse
├── storage.py          # add functions that load Task, mutate the JSON blob, save Task
├── business_rules.py   # add MAX_COMMENT_LENGTH + validation helper (same as Option A)
├── main.py              # same three routes as Option A
tests/
├── test_comments.py
```

No routers/comments.py split needed since there's no separate persistence module to justify it — everything still funnels through storage.py's existing Task functions.

### 3. Data model sketch

```python
class CommentItem(BaseModel):  # NOT a SQLModel table — lives inside comments_json
    id: str
    text: str
    created_at: datetime

class CommentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str
    # same validate_text as Option A (blank + MAX_COMMENT_LENGTH)

class CommentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    task_id: str
    text: str
    created_at: datetime

# Task gains one field:
class Task(SQLModel, table=True):
    ...
    comments_json: str = "[]"
```

Every comment operation becomes: session.get(Task, id) → json.loads(task.comments_json) → mutate list → json.dumps(...) back onto task.comments_json → session.commit().

### 4. Trade-offs vs. Option A

- ✅ Smallest possible diff: one nullable-ish column, zero new tables, easiest to read end-to-end in one file for a learning exercise.
- ❌ Every comment write (add or delete) requires loading the entire comment list for that task, mutating it in Python, and rewriting the whole blob — fine at learning-project scale, but it's a read-modify-write on a shared field, so it doesn't scale and is more error-prone than a targeted DELETE/INSERT.
- ❌ Weaker fit for US-5 (404s) and future growth: "does this comment exist" requires deserializing JSON and scanning a list rather than a straightforward session.get, and there's no natural place to add an index, foreign-key constraint, or ORDER BY created_at at the SQL level — ordering (US-2.1) has to be enforced in Python instead of the database.
