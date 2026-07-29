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


def test_get_all_tasks_filters_by_assignee() -> None:
    engine = get_engine()
    init_db(engine=engine)

    create_task(engine=engine, title="Task A", assignee="Alex")
    create_task(engine=engine, title="Task B", assignee="Sam")

    results = get_all_tasks(assignee="Alex")

    assert len(results) == 1
    assert results[0].title == "Task A"
    assert results[0].assignee == "Alex"


def test_get_all_tasks_search_matches_title() -> None:
    engine = get_engine()
    init_db(engine=engine)

    create_task(engine=engine, title="Fix login bug", description="Nothing special")
    create_task(engine=engine, title="Write docs", description="Update README")

    results = get_all_tasks(search="login")

    assert len(results) == 1
    assert results[0].title == "Fix login bug"


def test_get_all_tasks_search_matches_description_only() -> None:
    engine = get_engine()
    init_db(engine=engine)

    create_task(engine=engine, title="Unrelated title", description="Investigate login timeout")
    create_task(engine=engine, title="Write docs", description="Update README")

    results = get_all_tasks(search="login")

    assert len(results) == 1
    assert results[0].title == "Unrelated title"
    assert results[0].description == "Investigate login timeout"


def test_get_all_tasks_search_is_case_insensitive() -> None:
    engine = get_engine()
    init_db(engine=engine)

    create_task(engine=engine, title="URGENT: Fix Login", description="")

    results = get_all_tasks(search="urgent")

    assert len(results) == 1


def test_get_all_tasks_search_no_match_returns_empty_list() -> None:
    engine = get_engine()
    init_db(engine=engine)

    create_task(engine=engine, title="Write docs", description="Update README")

    results = get_all_tasks(search="nonexistent")

    assert results == []


def test_get_all_tasks_combines_status_priority_search_and_assignee() -> None:
    engine = get_engine()
    init_db(engine=engine)

    create_task(
        engine=engine,
        title="Fix login bug",
        status="InProgress",
        priority="High",
        assignee="Alex",
    )
    create_task(
        engine=engine,
        title="Fix login redirect",
        status="InProgress",
        priority="High",
        assignee="Sam",
    )
    create_task(
        engine=engine,
        title="Fix login crash",
        status="ToDo",
        priority="High",
        assignee="Alex",
    )

    results = get_all_tasks(status="InProgress", priority="High", search="login", assignee="Alex")

    assert len(results) == 1
    assert results[0].title == "Fix login bug"


def test_get_distinct_assignees_returns_sorted_unique_values() -> None:
    engine = get_engine()
    init_db(engine=engine)

    create_task(engine=engine, title="Task A", assignee="Sam")
    create_task(engine=engine, title="Task B", assignee="Alex")
    create_task(engine=engine, title="Task C", assignee="Sam")
    create_task(engine=engine, title="Task D", assignee=None)

    assignees = get_distinct_assignees()

    assert assignees == ["Alex", "Sam"]


def test_get_distinct_assignees_excludes_null_and_empty_values() -> None:
    engine = get_engine()
    init_db(engine=engine)

    create_task(engine=engine, title="Task A", assignee="Alex")
    create_task(engine=engine, title="Task B", assignee=None)
    create_task(engine=engine, title="Task C", assignee="")

    assignees = get_distinct_assignees()

    assert assignees == ["Alex"]
