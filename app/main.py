"""
Task Tracker API - Module 1 skeleton.

This is an intentionally minimal FastAPI application skeleton. Per
ADR-001 (docs/adr/001-storage-layer.md), the storage layer uses
SQLite + SQLModel with a local database file. This file wires up the
FastAPI app instance and a health check endpoint.
"""

from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app import storage
from app.business_rules import validate_status_transition
from app.models import TaskCreate, TaskPriority, TaskResponse, TaskStatus, TaskUpdate
from app.storage import get_engine, init_db

app = FastAPI(
    title="Task Tracker API",
    description="Module 1 learning project: a minimal task tracking REST API.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhostt:5500",
        "http://127.0.0.1:5500",
        "http://localhost:5173",
        "null",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)


@app.on_event("startup")
def startup_event() -> None:
    """Initialize the SQLite schema when the application starts."""
    init_db(engine=get_engine())


@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED, tags=["tasks"])
def create_task(payload: TaskCreate) -> TaskResponse:
    return storage.add_task(payload)


@app.get("/tasks", response_model=list[TaskResponse], tags=["tasks"])
def list_tasks(
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    search: str | None = None,
    assignee: str | None = None,
) -> list[TaskResponse]:
    return storage.get_all_tasks(status=status, priority=priority, search=search, assignee=assignee)


@app.get("/tasks/assignees", response_model=list[str], tags=["tasks"])
def list_assignees() -> list[str]:
    return storage.get_distinct_assignees()


@app.get("/tasks/{task_id}", response_model=TaskResponse, tags=["tasks"])
def get_task(task_id: str) -> TaskResponse:
    task = storage.get_task_by_id(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
    return task


@app.patch("/tasks/{task_id}", response_model=TaskResponse, tags=["tasks"])
def update_task(task_id: str, payload: TaskUpdate) -> TaskResponse:
    if payload.status is not None:
        existing_task = storage.get_task_by_id(task_id)
        if existing_task is None:
            raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
        validate_status_transition(existing_task.status, payload.status)
    
    task = storage.update_task(task_id, payload)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
    return task


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["tasks"])
def delete_task(task_id: str) -> None:
    if not storage.delete_task(task_id):
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")


@app.get("/health")
def health_check() -> dict:
    """
    Simple liveness check.

    Returns HTTP 200 with a JSON body containing a status flag and the
    current UTC timestamp in ISO 8601 format.
    """
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
