from fastapi.testclient import TestClient


def test_create_task_valid_returns_201_with_full_body(client: TestClient):
    response = client.post(
        "/tasks",
        json={
            "title": "Write tests",
            "description": "Create a complete integration test suite.",
            "status": "ToDo",
            "priority": "High",
            "assignee": "QA",
        },
    )

    assert response.status_code == 201

    body = response.json()
    assert body["id"]
    assert body["title"] == "Write tests"
    assert body["description"] == "Create a complete integration test suite."
    assert body["status"] == "ToDo"
    assert body["priority"] == "High"
    assert body["assignee"] == "QA"
    assert body["created_at"]
    assert body["updated_at"]


def test_create_task_missing_title_returns_422(client: TestClient):
    response = client.post("/tasks", json={"description": "No title provided"})

    assert response.status_code == 422


def test_create_task_blank_title_returns_422(client: TestClient):
    response = client.post("/tasks", json={"title": "   "})

    assert response.status_code == 422


def test_create_task_invalid_priority_returns_422(client: TestClient):
    response = client.post(
        "/tasks",
        json={"title": "Invalid priority", "priority": "Impossible"},
    )

    assert response.status_code == 422


def test_create_task_unknown_field_returns_422(client: TestClient):
    response = client.post(
        "/tasks",
        json={"title": "Unknown field", "unknown": "value"},
    )

    assert response.status_code == 422


def test_list_tasks_empty_returns_200_and_empty_list(client: TestClient):
    response = client.get("/tasks")

    assert response.status_code == 200
    assert response.json() == []


def test_list_tasks_filter_by_status_no_match_returns_200_and_empty_list(client: TestClient):
    client.post("/tasks", json={"title": "Only todo"})

    response = client.get("/tasks", params={"status": "Done"})

    assert response.status_code == 200
    assert response.json() == []


def test_list_tasks_filter_by_priority_returns_only_matches(client: TestClient):
    client.post("/tasks", json={"title": "Low priority", "priority": "Low"})
    client.post("/tasks", json={"title": "High priority", "priority": "High"})

    response = client.get("/tasks", params={"priority": "High"})

    assert response.status_code == 200

    body = response.json()
    assert len(body) == 1
    assert body[0]["title"] == "High priority"
    assert body[0]["priority"] == "High"


def test_list_tasks_filter_by_assignee_returns_only_matches(client: TestClient):
    client.post("/tasks", json={"title": "Alex's task", "assignee": "Alex"})
    client.post("/tasks", json={"title": "Sam's task", "assignee": "Sam"})

    response = client.get("/tasks", params={"assignee": "Alex"})

    assert response.status_code == 200

    body = response.json()
    assert len(body) == 1
    assert body[0]["title"] == "Alex's task"
    assert body[0]["assignee"] == "Alex"


def test_list_tasks_filter_by_search_matches_title(client: TestClient):
    client.post("/tasks", json={"title": "Fix login bug"})
    client.post("/tasks", json={"title": "Write docs"})

    response = client.get("/tasks", params={"search": "login"})

    assert response.status_code == 200

    body = response.json()
    assert len(body) == 1
    assert body[0]["title"] == "Fix login bug"


def test_list_tasks_filter_by_search_matches_description(client: TestClient):
    client.post(
        "/tasks",
        json={"title": "Unrelated title", "description": "Investigate login timeout"},
    )
    client.post("/tasks", json={"title": "Write docs", "description": "Update README"})

    response = client.get("/tasks", params={"search": "login"})

    assert response.status_code == 200

    body = response.json()
    assert len(body) == 1
    assert body[0]["title"] == "Unrelated title"


def test_list_tasks_filter_by_search_no_match_returns_empty_list(client: TestClient):
    client.post("/tasks", json={"title": "Write docs"})

    response = client.get("/tasks", params={"search": "nonexistent"})

    assert response.status_code == 200
    assert response.json() == []


def test_list_tasks_combines_status_priority_search_and_assignee(client: TestClient):
    client.post(
        "/tasks",
        json={"title": "Fix login bug", "status": "ToDo", "priority": "High", "assignee": "Alex"},
    )
    client.post(
        "/tasks",
        json={"title": "Fix login redirect", "status": "ToDo", "priority": "High", "assignee": "Sam"},
    )
    client.post(
        "/tasks",
        json={"title": "Fix login crash", "status": "ToDo", "priority": "Low", "assignee": "Alex"},
    )

    response = client.get(
        "/tasks",
        params={"status": "ToDo", "priority": "High", "search": "login", "assignee": "Alex"},
    )

    assert response.status_code == 200

    body = response.json()
    assert len(body) == 1
    assert body[0]["title"] == "Fix login bug"


def test_list_assignees_returns_sorted_unique_values(client: TestClient):
    client.post("/tasks", json={"title": "Task A", "assignee": "Sam"})
    client.post("/tasks", json={"title": "Task B", "assignee": "Alex"})
    client.post("/tasks", json={"title": "Task C", "assignee": "Sam"})
    client.post("/tasks", json={"title": "Task D"})

    response = client.get("/tasks/assignees")

    assert response.status_code == 200
    assert response.json() == ["Alex", "Sam"]


def test_list_assignees_empty_returns_200_and_empty_list(client: TestClient):
    response = client.get("/tasks/assignees")

    assert response.status_code == 200
    assert response.json() == []


def test_get_task_by_id_returns_task(client: TestClient, created_task: dict):
    task_id = created_task["id"]

    response = client.get(f"/tasks/{task_id}")

    assert response.status_code == 200
    assert response.json()["id"] == task_id
    assert response.json()["title"] == "fixture task"


def test_get_task_by_id_not_found_returns_404_with_detail(client: TestClient):
    response = client.get("/tasks/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Task with id 999999 not found"


def test_patch_partial_update_keeps_other_fields(client: TestClient, created_task: dict):
    task_id = created_task["id"]

    response = client.patch(
        f"/tasks/{task_id}",
        json={"description": "Updated description"},
    )

    assert response.status_code == 200

    body = response.json()
    assert body["id"] == task_id
    assert body["description"] == "Updated description"
    assert body["title"] == created_task["title"]
    assert body["status"] == created_task["status"]
    assert body["priority"] == created_task["priority"]
    assert body["assignee"] == created_task["assignee"]


def test_patch_not_found_returns_404(client: TestClient):
    response = client.patch("/tasks/999999", json={"title": "Does not exist"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Task with id 999999 not found"


def test_patch_valid_transition_todo_to_inprogress_returns_200(client: TestClient, created_task: dict):
    task_id = created_task["id"]

    response = client.patch(
        f"/tasks/{task_id}",
        json={"status": "InProgress"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "InProgress"


def test_patch_invalid_transition_todo_to_done_returns_422(client: TestClient, created_task: dict):
    task_id = created_task["id"]

    response = client.patch(
        f"/tasks/{task_id}",
        json={"status": "Done"},
    )

    assert response.status_code == 422


def test_patch_same_status_returns_200(client: TestClient, created_task: dict):
    task_id = created_task["id"]

    response = client.patch(
        f"/tasks/{task_id}",
        json={"status": "ToDo"},
    )

    assert response.status_code == 200


def test_delete_existing_returns_204_no_body(client: TestClient, created_task: dict):
    task_id = created_task["id"]

    response = client.delete(f"/tasks/{task_id}")

    assert response.status_code == 204
    assert response.content == b""


def test_delete_missing_returns_404(client: TestClient):
    response = client.delete("/tasks/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Task with id 999999 not found"
