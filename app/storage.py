from __future__ import annotations

import os
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Optional

from sqlalchemy import func, or_
from sqlmodel import Session, SQLModel, create_engine, delete, select

from app.models import (
    Comment,
    CommentCreate,
    CommentResponse,
    Task,
    TaskCreate,
    TaskPriority,
    TaskResponse,
    TaskStatus,
    TaskUpdate,
)


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


def _task_to_response(task: Task, comment_count: int) -> TaskResponse:
    return TaskResponse(
        id=str(task.id),
        title=task.title,
        description=task.description or "",
        status=TaskStatus(_coerce_status(task.status)),
        priority=TaskPriority(_coerce_priority(task.priority)),
        assignee=task.assignee,
        created_at=task.created_at,
        updated_at=task.updated_at,
        comment_count=comment_count,
    )


def _comment_count_for_task(session: Session, task_id: int) -> int:
    statement = select(func.count(Comment.id)).where(Comment.task_id == task_id)
    return session.exec(statement).one()


def _comment_counts_by_task_id(session: Session, task_ids: list[int]) -> dict[int, int]:
    if not task_ids:
        return {}

    statement = (
        select(Comment.task_id, func.count(Comment.id))
        .where(Comment.task_id.in_(task_ids))
        .group_by(Comment.task_id)
    )
    return dict(session.exec(statement).all())


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
        return _task_to_response(task, comment_count=0)


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
        comment_counts = _comment_counts_by_task_id(session, [task.id for task in tasks])
        return [_task_to_response(task, comment_counts.get(task.id, 0)) for task in tasks]


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
        comment_count = _comment_count_for_task(session, task_id_int)
        return _task_to_response(task, comment_count)


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
            comment_count = _comment_count_for_task(session, task_id_int)
            return _task_to_response(task, comment_count)

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
        comment_count = _comment_count_for_task(session, task_id_int)
        return _task_to_response(task, comment_count)


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


def _comment_to_response(comment: Comment) -> CommentResponse:
    return CommentResponse(
        id=str(comment.id),
        task_id=str(comment.task_id),
        text=comment.text,
        created_at=comment.created_at,
    )


def add_comment(task_id: str, payload: CommentCreate) -> Optional[CommentResponse]:
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

        comment = Comment(task_id=task_id_int, text=payload.text)
        session.add(comment)
        session.commit()
        session.refresh(comment)
        return _comment_to_response(comment)


def get_comments_for_task(task_id: str) -> Optional[list[CommentResponse]]:
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

        statement = select(Comment).where(Comment.task_id == task_id_int).order_by(Comment.created_at)
        comments = session.exec(statement).all()
        return [_comment_to_response(comment) for comment in comments]


def delete_comment(comment_id: str) -> bool:
    try:
        comment_id_int = int(comment_id)
    except (TypeError, ValueError):
        return False

    engine = get_engine()
    init_db(engine=engine)

    with Session(engine) as session:
        comment = session.get(Comment, comment_id_int)
        if comment is None:
            return False
        session.delete(comment)
        session.commit()
        return True


def _reset() -> None:
    engine = get_engine()
    init_db(engine=engine)

    with Session(engine) as session:
        session.exec(delete(Comment))
        session.exec(delete(Task))
        session.commit()
