import pytest
import os
import sys


sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

from app import app, reset_data  # noqa: E402


@pytest.fixture
def client():
    app.config["TESTING"] = True
    reset_data()

    with app.test_client() as client:
        yield client

    reset_data()


def test_health_route(client):
    response = client.get("/health")

    assert response.status_code == 201
    assert response.get_json() == {"status": "ok"}


def test_add_valid_assignment(client):
    data = {
        "subject": "Mathematics",
        "name": "Assignment 1",
        "due_date": "2026-10-15",
    }

    response = client.post("/add", data=data)

    assert response.status_code == 302
    assert client.get("/api/assignments").get_json() == [
        {
            "id": 1,
            "subject": "Mathematics",
            "name": "Assignment 1",
            "due_date": "2026-10-15",
            "completed": False,
        }
    ]


def test_add_invalid_assignment_rejected(client):
    data = {
        "subject": "",
        "name": "",
        "due_date": "2026-10-15",
    }

    response = client.post("/add", data=data)

    assert response.status_code == 400
    assert client.get("/api/assignments").get_json() == []


def test_add_invalid_date_rejected(client):
    data = {
        "subject": "Mathematics",
        "name": "Assignment 1",
        "due_date": "15-10-2026",
    }

    response = client.post("/add", data=data)

    assert response.status_code == 400
    assert client.get("/api/assignments").get_json() == []


def test_complete_and_delete_assignment(client):
    data = {
        "subject": "Mathematics",
        "name": "Assignment 1",
        "due_date": "2026-10-15",
    }

    client.post("/add", data=data)

    complete_response = client.post("/complete/1")

    assert complete_response.status_code == 302
    assert client.get("/api/assignments").get_json()[0]["completed"] is True

    delete_response = client.post("/delete/1")

    assert delete_response.status_code == 302
    assert client.get("/api/assignments").get_json() == []


def test_assignments_api_returns_json(client):
    data = {
        "subject": "Data Structures",
        "name": "Assignment 1",
        "due_date": "2026-10-20",
    }

    client.post("/add", data=data)

    response = client.get("/api/assignments")

    assert response.status_code == 200
    assert response.is_json
    assert response.get_json()[0]["subject"] == "Data Structures"


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
    from datetime import date, timedelta

    past_date = (date.today() - timedelta(days=1)).isoformat()

    data = {
        "subject": "Mathematics",
        "name": "Assignment 2",
        "due_date": past_date,
    }

    response = client.post("/add", data=data)

    assert response.status_code == 400
    assert client.get("/api/assignments").get_json() == []


def test_add_rejects_duplicate_assignment(client):
    data = {
        "subject": "Mathematics",
        "name": "Assignment 1",
        "due_date": "2026-10-15",
    }

    first_response = client.post("/add", data=data)

    assert first_response.status_code == 302

    duplicate_response = client.post("/add", data=data)

    assert duplicate_response.status_code == 400
    assert client.get("/api/assignments").get_json() == [
        {
            "id": 1,
            "subject": "Mathematics",
            "name": "Assignment 1",
            "due_date": "2026-10-15",
            "completed": False,
        }
    ]


def test_add_rejects_case_insensitive_duplicate(client):
    first_data = {
        "subject": "Mathematics",
        "name": "Assignment 1",
        "due_date": "2026-10-20",
    }

    second_data = {
        "subject": "mathematics",
        "name": "assignment 1",
        "due_date": "2026-10-25",
    }

    first_response = client.post("/add", data=first_data)
    second_response = client.post("/add", data=second_data)

    assert first_response.status_code == 302
    assert second_response.status_code == 400
    assert len(client.get("/api/assignments").get_json()) == 1
