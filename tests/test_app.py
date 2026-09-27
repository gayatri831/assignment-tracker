
import os
import sys
from datetime import date, timedelta
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app, reset_data  # noqa: E402


@pytest.fixture
def client():
    reset_data()
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client
    reset_data()


def test_health_route(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_add_valid_assignment(client):
    response = client.post(
        "/add",
        data={
            "subject": "Mathematics",
            "name": "Assignment 1",
            "due_date": "2026-10-15",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    data = client.get("/api/assignments").get_json()
    assert len(data) == 1
    assert data[0]["subject"] == "Mathematics"
    assert data[0]["name"] == "Assignment 1"
    assert data[0]["completed"] is False


def test_add_invalid_assignment_rejected(client):
    response = client.post(
        "/add",
        data={
            "subject": "",
            "name": "Assignment 1",
            "due_date": "2026-10-15",
        },
    )
    assert response.status_code == 400

    data = client.get("/api/assignments").get_json()
    assert data == []


def test_add_invalid_date_rejected(client):
    response = client.post(
        "/add",
        data={
            "subject": "Physics",
            "name": "Lab report",
            "due_date": "15-10-2026",
        },
    )
    assert response.status_code == 400


def test_complete_and_delete_assignment(client):
    client.post(
        "/add",
        data={
            "subject": "Physics",
            "name": "Lab report",
            "due_date": "2026-11-01",
        },
    )
    data = client.get("/api/assignments").get_json()
    assignment_id = data[0]["id"]

    client.post(f"/complete/{assignment_id}")
    data = client.get("/api/assignments").get_json()
    assert data[0]["completed"] is True

    client.post(f"/delete/{assignment_id}")
    data = client.get("/api/assignments").get_json()
    assert data == []


def test_assignments_api_returns_json(client):
    response = client.get("/api/assignments")

    assert response.status_code == 200
    assert response.is_json
    assert response.get_json() == []


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("subject", "S" * 61),
        ("name", "A" * 101),
    ],
)
def test_add_rejects_text_that_is_too_long(client, field, value):
    data = {
        "subject": "Mathematics",
        "name": "Assignment 1",
        "due_date": "2026-10-15",
    }
    data[field] = value

    response = client.post("/add", data=data)

    assert response.status_code == 400
    assert client.get("/api/assignments").get_json() == []


def test_add_rejects_impossible_date(client):
    data = {
        "subject": "Mathematics",
        "name": "Assignment 1",
        "due_date": "2026-02-30",
    }

    response = client.post("/add", data=data)

    assert response.status_code == 400
    assert client.get("/api/assignments").get_json() == []


def test_add_rejects_past_due_date(client):
    past_date = (date.today() - timedelta(days=1)).isoformat()

    data = {
        "subject": "Mathematics",
        "name": "Assignment 2",
        "due_date": past_date,
    }

    response = client.post("/add", data=data)

    assert response.status_code == 400
    assert client.get("/api/assignments").get_json() == []
