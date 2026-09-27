"""
Assignment Tracker - Academic Assignment Deadline Tracker

A small Flask app that lets a student add assignments, mark them
complete, delete them, and view upcoming deadlines. Built for CCA 2.
"""
import os
import re
from datetime import datetime

from flask import Flask, jsonify, redirect, render_template, request, url_for

app = Flask(__name__)

# --- In-memory data store -------------------------------------------------
# Each assignment looks like:
# {"id": 1, "subject": "Maths", "name": "Assignment 1",
#  "due_date": "2026-10-15", "completed": False}
assignments = []
_next_id = 1


def reset_data():
    """Clear all in-memory data. Used by the test suite for a clean slate."""
    global assignments, _next_id
    assignments = []
    _next_id = 1


def _validate_assignment(form):
    """Validate the incoming form data for a new assignment.

    Returns a tuple of (is_valid, error_message).
    """
    subject = (form.get("subject") or "").strip()
    name = (form.get("name") or "").strip()
    due_date = (form.get("due_date") or "").strip()

    if not subject:
        return False, "Subject is required."

    if not name:
        return False, "Assignment name is required."

    if len(subject) > 60:
        return False, "Subject must be 60 characters or fewer."

    if len(name) > 100:
        return False, "Assignment name must be 100 characters or fewer."

    if not due_date:
        return False, "Due date is required."

    if not re.match(r"^\d{4}-\d{2}-\d{2}$", due_date):
        return False, "Due date must be in YYYY-MM-DD format."

    try:
        parsed_date = datetime.strptime(
            due_date, "%Y-%m-%d"
        ).date()
    except ValueError:
        return False, "Due date is not a real calendar date."

    if parsed_date < datetime.today().date():
        return False, "Due date cannot be in the past."

    # Prevent duplicate assignments with the same subject and name.
    for assignment in assignments:
        same_subject = (
            assignment["subject"].strip().casefold()
            == subject.casefold()
        )
        same_name = (
            assignment["name"].strip().casefold()
            == name.casefold()
        )

        if same_subject and same_name:
            return False, (
                "An assignment with the same subject and name "
                "already exists."
            )

    return True, None


def _sorted_assignments():
    """Pending assignments first, then everything sorted by due date."""
    return sorted(
        assignments,
        key=lambda a: (a["completed"], a["due_date"]),
    )


def _render_index(error=None, status=200):
    pending = [a for a in assignments if not a["completed"]]
    completed = [a for a in assignments if a["completed"]]
    commit_id = os.environ.get("RENDER_GIT_COMMIT", "local-dev")[:7]

    return render_template(
        "index.html",
        assignments=_sorted_assignments(),
        pending_count=len(pending),
        completed_count=len(completed),
        total_count=len(assignments),
        commit_id=commit_id,
        error=error,
    ), status


@app.route("/")
def index():
    return _render_index()


@app.route("/add", methods=["POST"])
def add_assignment():
    global _next_id

    is_valid, error = _validate_assignment(request.form)

    if not is_valid:
        return _render_index(error=error, status=400)

    assignments.append({
        "id": _next_id,
        "subject": request.form["subject"].strip(),
        "name": request.form["name"].strip(),
        "due_date": request.form["due_date"].strip(),
        "completed": False,
    })

    _next_id += 1

    return redirect(url_for("index"))


@app.route("/complete/<int:assignment_id>", methods=["POST"])
def complete_assignment(assignment_id):
    for assignment in assignments:
        if assignment["id"] == assignment_id:
            assignment["completed"] = not assignment["completed"]
            break

    return redirect(url_for("index"))


@app.route("/delete/<int:assignment_id>", methods=["POST"])
def delete_assignment(assignment_id):
    global assignments

    assignments = [
        assignment
        for assignment in assignments
        if assignment["id"] != assignment_id
    ]

    return redirect(url_for("index"))


@app.route("/api/assignments")
def api_assignments():
    return jsonify(assignments)


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=True,
    )
