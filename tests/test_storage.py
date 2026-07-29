from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

from app.storage import create_task, get_all_tasks, get_distinct_assignees, get_engine, get_task_by_id, init_db


def test_database_initializes_and_persists_a_task(tmp_path: Path) -> None:
    database_path = tmp_path / "tasks.db"
    engine = create_engine(f"sqlite:///{database_path}")

    init_db(engine=engine)

    created_task = create_task(
        engine=engine,
        title="Write module notes",
        description="Document the storage layer choices.",
        status="ToDo",
        priority="Medium",
        assignee="Alex",
    )

    assert created_task.id is not None
    assert created_task.title == "Write module notes"

    stored_task = get_task_by_id(engine=engine, task_id=created_task.id)

    assert stored_task is not None
    assert stored_task.title == "Write module notes"
    assert stored_task.description == "Document the storage layer choices."
    assert stored_task.status == "ToDo"
    assert stored_task.priority == "Medium"
    assert stored_task.assignee == "Alex"
    assert SQLModel.metadata.tables["tasks"].name == "tasks"


def test_created_task_has_zero_comment_count(tmp_path: Path) -> None:
    database_path = tmp_path / "tasks.db"
    engine = create_engine(f"sqlite:///{database_path}")
    init_db(engine=engine)

    created_task = create_task(engine=engine, title="No comments yet")

    assert created_task.comment_count == 0

