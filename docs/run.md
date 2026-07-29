# Task Tracker API - Commands

## Start Server

```cmd
cd /d C:\Users\Lenovo\Desktop\aub coding with ai\task-tracker
uvicorn app.main:app --reload
```

Server: http://127.0.0.1:8000
Swagger UI: http://127.0.0.1:8000/docs

---

## POST /tasks - Create Task

```cmd
curl -X POST http://127.0.0.1:8000/tasks -H "Content-Type: application/json" -d "{\"title\":\"My Task\",\"description\":\"Description\",\"status\":\"ToDo\",\"priority\":\"Medium\",\"assignee\":\"Name\"}"
```

Status Values: `ToDo`, `InProgress`, `Done`
Priority Values: `Low`, `Medium`, `High`

---

## GET /tasks - List Tasks

List all:
```cmd
curl http://127.0.0.1:8000/tasks
```

By status:
```cmd
curl "http://127.0.0.1:8000/tasks?status=ToDo"
```

By priority:
```cmd
curl "http://127.0.0.1:8000/tasks?priority=High"
```

By both:
```cmd
curl "http://127.0.0.1:8000/tasks?status=InProgress&priority=High"
```

By assignee (exact match):
```cmd
curl "http://127.0.0.1:8000/tasks?assignee=Alex"
```

By search (matches title or description, case-insensitive):
```cmd
curl "http://127.0.0.1:8000/tasks?search=login"
```

Combined filters:
```cmd
curl "http://127.0.0.1:8000/tasks?status=InProgress&priority=High&assignee=Alex&search=login"
```

---

## GET /tasks/{task_id} - Get Single Task

```cmd
curl http://127.0.0.1:8000/tasks/1
```

Returns 404 if task not found.

---

## PATCH /tasks/{task_id} - Update Task

```cmd
curl -X PATCH http://127.0.0.1:8000/tasks/1 -H "Content-Type: application/json" -d "{\"title\":\"Updated Title\",\"status\":\"InProgress\"}"
```

Only include fields to update. Returns 404 if task not found.

---

## DELETE /tasks/{task_id} - Delete Task

```cmd
curl -X DELETE http://127.0.0.1:8000/tasks/1
```

Returns 204 No Content on success. Returns 404 if task not found.

---

## POST /tasks/{task_id}/comments - Add Comment

```cmd
curl -X POST http://127.0.0.1:8000/tasks/1/comments -H "Content-Type: application/json" -d "{\"text\":\"This is a comment\"}"
```

Text must be non-blank and 1000 characters or fewer. Returns 422 if blank or too long. Returns 404 if task not found.

---

## GET /tasks/{task_id}/comments - List Comments

```cmd
curl http://127.0.0.1:8000/tasks/1/comments
```

Returns comments ordered oldest first. Returns an empty list if the task has no comments. Returns 404 if task not found.

---

## DELETE /comments/{comment_id} - Delete Comment

```cmd
curl -X DELETE http://127.0.0.1:8000/comments/1
```

Returns 204 No Content on success. Returns 404 if comment not found.

---

## Check Database

```cmd
cd /d C:\Users\Lenovo\Desktop\aub coding with ai\task-tracker
"C:\Users\Lenovo\Desktop\aub coding with ai\task-tracker\venv\Scripts\python.exe" -c "import sqlite3; from pathlib import Path; import app.storage as storage; db = Path(storage.__file__).resolve().parent.parent / 'tasks.db'; print('Database:', db); conn = sqlite3.connect(str(db)); print('Total rows:', conn.execute('select count(*) from tasks').fetchone()[0]); conn.close()"
```

Database file: `C:\Users\Lenovo\Desktop\aub coding with ai\task-tracker\tasks.db`

If viewer shows 0 rows, refresh your database viewer or reopen the file.

---

## Future Endpoints

Will add commands for:
- GET /tasks/{id}
- PUT /tasks/{id}
- DELETE /tasks/{id}
