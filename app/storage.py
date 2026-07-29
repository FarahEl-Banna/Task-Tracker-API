from __future__ import annotations

import os
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Optional

from sqlalchemy import or_
from sqlmodel import Session, SQLModel, create_engine, delete, select

from app.models import Task, TaskCreate, TaskPriority, TaskResponse, TaskStatus, TaskUpdate


@lru_cache(maxsize=1)
def get_engine():
    db_path = Path(__file__).resolve().parent.parent / "tasks.db"
    return create_engine(f"sqlite:///{db_path}")


def init_db(engine=None):
    if engine is None:
        engine = get_engine()
    SQLModel.metadata.create_all(engine)


def _coerce_status(value: TaskStatus | str | None) -> str:
    if isinstance(value, TaskStatus):
        return value.value
    if isinstance(value, str):
        normalized = value.strip().lower()
        for member in TaskStatus:
            if normalized in {member.name.lower(), member.value.lower()}:
                return member.value
        return value
    return TaskStatus.TODO.value


def _coerce_priority(value: TaskPriority | str | None) -> str:
    if isinstance(value, TaskPriority):
        return value.value
    if isinstance(value, str):
        normalized = value.strip().lower()
        for member in TaskPriority:
            if normalized in {member.name.lower(), member.value.lower()}:
                return member.value
        return value
    return TaskPriority.MEDIUM.value


def _task_to_response(task: Task) -> TaskResponse:
    return TaskResponse(
        id=str(task.id),
        title=task.title,
        description=task.description or "",
        status=TaskStatus(_coerce_status(task.status)),
        priority=TaskPriority(_coerce_priority(task.priority)),
        assignee=task.assignee,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


def create_task(
    engine=None,
    title: str = "",
    description: str | None = None,
    status: TaskStatus | str | None = None,
    priority: TaskPriority | str | None = None,
    assignee: str | None = None,
) -> TaskResponse:
    if engine is None:
        engine = get_engine()
    init_db(engine=engine)

    with Session(engine) as session:
        now = datetime.now(timezone.utc)
        task = Task(
            title=title,
            description=description or "",
            status=_coerce_status(status),
            priority=_coerce_priority(priority),
            assignee=assignee,
            created_at=now,
            updated_at=now,
        )
        session.add(task)
        session.commit()
        session.refresh(task)
        return _task_to_response(task)


def add_task(payload: TaskCreate) -> TaskResponse:
    return create_task(
        engine=get_engine(),
        title=payload.title,
        description=payload.description,
        status=payload.status,
        priority=payload.priority,
        assignee=payload.assignee,
    )


def get_all_tasks(
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    search: str | None = None,
    assignee: str | None = None,
) -> list[TaskResponse]:
    engine = get_engine()
    init_db(engine=engine)

    with Session(engine) as session:
        statement = select(Task)
        if status is not None:
            statement = statement.where(Task.status == _coerce_status(status))
        if priority is not None:
            statement = statement.where(Task.priority == _coerce_priority(priority))
        if assignee is not None:
            statement = statement.where(Task.assignee == assignee)
        if search is not None and search.strip():
            search_term = f"%{search.strip()}%"
            statement = statement.where(
                or_(Task.title.ilike(search_term), Task.description.ilike(search_term))
            )

        statement = statement.order_by(Task.created_at)
        tasks = session.exec(statement).all()
        return [_task_to_response(task) for task in tasks]


def get_distinct_assignees() -> list[str]:
    engine = get_engine()
    init_db(engine=engine)

    with Session(engine) as session:
        statement = select(Task.assignee).distinct()
        results = session.exec(statement).all()
        return sorted({assignee for assignee in results if assignee})


def get_task_by_id(task_id: str, engine=None) -> Optional[TaskResponse]:
    if task_id is None:
        return None

    try:
        task_id_int = int(task_id)
    except (TypeError, ValueError):
        return None

    if engine is None:
        engine = get_engine()
    init_db(engine=engine)

    with Session(engine) as session:
        task = session.get(Task, task_id_int)
        if task is None:
            return None
        return _task_to_response(task)


def update_task(task_id: str, payload: TaskUpdate) -> Optional[TaskResponse]:
    try:
        task_id_int = int(task_id)
    except (TypeError, ValueError):
        return None

    engine = get_engine()
    init_db(engine=engine)

    with Session(engine) as session:
        task = session.get(Task, task_id_int)
        if task is None:
            return None

        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            return _task_to_response(task)

        for field, value in updates.items():
            if field == "status":
                setattr(task, field, _coerce_status(value))
            elif field == "priority":
                setattr(task, field, _coerce_priority(value))
            else:
                setattr(task, field, value)

        task.updated_at = datetime.now(timezone.utc)
        session.add(task)
        session.commit()
        session.refresh(task)
        return _task_to_response(task)


def delete_task(task_id: str) -> bool:
    try:
        task_id_int = int(task_id)
    except (TypeError, ValueError):
        return False

    engine = get_engine()
    init_db(engine=engine)

    with Session(engine) as session:
        task = session.get(Task, task_id_int)
        if task is None:
            return False
        session.delete(task)
        session.commit()
        return True


def _reset() -> None:
    engine = get_engine()
    init_db(engine=engine)

    with Session(engine) as session:
        session.exec(delete(Task))
        session.commit()
