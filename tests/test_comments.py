from fastapi.testclient import TestClient


def test_add_comment_valid_returns_201_with_full_body(client: TestClient, created_task: dict):
    task_id = created_task["id"]

    response = client.post(f"/tasks/{task_id}/comments", json={"text": "First comment"})

    assert response.status_code == 201

    body = response.json()
    assert body["id"]
    assert body["task_id"] == task_id
    assert body["text"] == "First comment"
    assert body["created_at"]


def test_add_comment_blank_text_returns_422(client: TestClient, created_task: dict):
    task_id = created_task["id"]

    response = client.post(f"/tasks/{task_id}/comments", json={"text": "   "})

    assert response.status_code == 422


def test_add_comment_unknown_field_returns_422(client: TestClient, created_task: dict):
    task_id = created_task["id"]

    response = client.post(
        f"/tasks/{task_id}/comments",
        json={"text": "Valid text", "unknown": "value"},
    )

    assert response.status_code == 422


def test_add_comment_exactly_1000_chars_returns_201(client: TestClient, created_task: dict):
    task_id = created_task["id"]

    response = client.post(f"/tasks/{task_id}/comments", json={"text": "x" * 1000})

    assert response.status_code == 201
    assert len(response.json()["text"]) == 1000


def test_add_comment_1001_chars_returns_422(client: TestClient, created_task: dict):
    task_id = created_task["id"]

    response = client.post(f"/tasks/{task_id}/comments", json={"text": "x" * 1001})

    assert response.status_code == 422


def test_add_comment_task_not_found_returns_404(client: TestClient):
    response = client.post("/tasks/999999/comments", json={"text": "Orphan comment"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Task with id 999999 not found"


def test_list_comments_empty_returns_200_and_empty_list(client: TestClient, created_task: dict):
    task_id = created_task["id"]

    response = client.get(f"/tasks/{task_id}/comments")

    assert response.status_code == 200
    assert response.json() == []


def test_list_comments_returns_ordered_oldest_first(client: TestClient, created_task: dict):
    task_id = created_task["id"]

    client.post(f"/tasks/{task_id}/comments", json={"text": "first"})
    client.post(f"/tasks/{task_id}/comments", json={"text": "second"})
    client.post(f"/tasks/{task_id}/comments", json={"text": "third"})

    response = client.get(f"/tasks/{task_id}/comments")

    assert response.status_code == 200

    body = response.json()
    assert [comment["text"] for comment in body] == ["first", "second", "third"]


def test_list_comments_task_not_found_returns_404(client: TestClient):
    response = client.get("/tasks/999999/comments")

    assert response.status_code == 404
    assert response.json()["detail"] == "Task with id 999999 not found"


def test_delete_comment_returns_204(client: TestClient, created_comment: dict):
    comment_id = created_comment["id"]

    response = client.delete(f"/comments/{comment_id}")

    assert response.status_code == 204
    assert response.content == b""


def test_delete_comment_not_found_returns_404(client: TestClient):
    response = client.delete("/comments/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Comment with id 999999 not found"


def test_delete_comment_does_not_affect_other_comments(client: TestClient, created_task: dict):
    task_id = created_task["id"]

    keep = client.post(f"/tasks/{task_id}/comments", json={"text": "keep me"}).json()
    remove = client.post(f"/tasks/{task_id}/comments", json={"text": "remove me"}).json()

    delete_response = client.delete(f"/comments/{remove['id']}")
    assert delete_response.status_code == 204

    remaining = client.get(f"/tasks/{task_id}/comments").json()
    assert [comment["id"] for comment in remaining] == [keep["id"]]

    task_response = client.get(f"/tasks/{task_id}")
    assert task_response.status_code == 200
