import pytest
from app import create_app


@pytest.fixture
def client():
    return create_app({"TESTING": True, "VERSION": "test-version"}).test_client()


def test_home_health_version(client):
    assert client.get("/").status_code == 200
    assert client.get("/health").json == {"status": "healthy"}
    assert client.get("/version").json == {"version": "test-version"}


def test_task_lifecycle(client):
    assert client.get("/api/tasks").json == {"tasks": []}
    result = client.post("/api/tasks", json={"title": "  Ship the pipeline  "})
    assert result.status_code == 201
    task = result.json["task"]
    assert task == {"id": 1, "title": "Ship the pipeline", "completed": False}
    assert client.get("/api/tasks").json["tasks"] == [task]
    assert client.patch("/api/tasks/1", json={"completed": True}).json["task"]["completed"] is True
    assert client.patch("/api/tasks/1", json={"completed": False}).json["task"]["completed"] is False
    assert client.delete("/api/tasks/1").status_code == 204
    assert client.get("/api/tasks").json["tasks"] == []


@pytest.mark.parametrize("body", [None, [], "text", {}, {"title": ""}, {"title": "  "}, {"title": 1}, {"title": "a" * 201}, {"title": "ok", "extra": True}])
def test_invalid_creation(client, body):
    assert client.post("/api/tasks", json=body).status_code == 400
    assert client.get("/api/tasks").json["tasks"] == []


@pytest.mark.parametrize("body", [{}, [], {"completed": "true"}, {"completed": 1}, {"completed": None}, {"completed": True, "title": "x"}])
def test_invalid_completion(client, body):
    client.post("/api/tasks", json={"title": "Task"})
    assert client.patch("/api/tasks/1", json=body).status_code == 400
    assert client.get("/api/tasks").json["tasks"][0]["completed"] is False


def test_missing_task(client):
    assert client.patch("/api/tasks/99", json={"completed": True}).status_code == 404
    assert client.delete("/api/tasks/99").status_code == 404


def test_bad_json_and_size_limit(client):
    assert client.post("/api/tasks", data="{", content_type="application/json").status_code == 400
    assert client.post("/api/tasks", data="x" * 17000, content_type="application/json").status_code == 413
    assert client.get("/api/missing").json.get("error")


def test_isolated_instances_and_unique_ids(client):
    client.post("/api/tasks", json={"title": "First"})
    client.delete("/api/tasks/1")
    assert client.post("/api/tasks", json={"title": "Second"}).json["task"]["id"] == 2
    assert create_app({"TESTING": True}).test_client().get("/api/tasks").json["tasks"] == []
