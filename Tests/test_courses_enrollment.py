from unittest.mock import MagicMock
import app as flask_app


def test_courses_requires_login(client):
    resp = client.get("/courses", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_courses_list_filtered_by_department(client, monkeypatch, employee_user):
    with client.session_transaction() as sess:
        sess["employee"] = employee_user

    all_courses = [
        {"id": 1, "title": "IT Course 1", "department": "IT"},
        {"id": 2, "title": "HR Course 1", "department": "HR"},
    ]

    monkeypatch.setattr(flask_app, "api_get", lambda path: all_courses if path == "courses" else [])

    resp = client.get("/courses")
    assert resp.status_code == 200
    # Only IT courses should be rendered
    body = resp.data.decode("utf-8")
    assert "IT Course 1" in body
    assert "HR Course 1" not in body


def test_courses_enroll_success(client, monkeypatch, employee_user):
    with client.session_transaction() as sess:
        sess["employee"] = employee_user

    mock_resp = MagicMock()
    mock_resp.status_code = 201

    monkeypatch.setattr(flask_app, "api_post", lambda path, data: mock_resp)
    monkeypatch.setattr(flask_app, "api_get", lambda path: [])

    resp = client.post("/courses", data={"course_id": "1"}, follow_redirects=False)
    assert resp.status_code == 302
    assert "/courses" in resp.headers["Location"]


def test_manage_courses_get_admin_only(client, monkeypatch, admin_user):
    with client.session_transaction() as sess:
        sess["employee"] = admin_user

    monkeypatch.setattr(flask_app, "api_get", lambda path: [])

    resp = client.get("/manage-courses")
    assert resp.status_code == 200


def test_manage_courses_create_course_success(client, monkeypatch, admin_user):
    with client.session_transaction() as sess:
        sess["employee"] = admin_user

    mock_resp = MagicMock()
    mock_resp.status_code = 201

    monkeypatch.setattr(flask_app, "api_get", lambda path: [])
    monkeypatch.setattr(flask_app, "api_post", lambda path, data: mock_resp)

    resp = client.post(
        "/manage-courses",
        data={
            "title": "New Course",
            "description": "Desc",
            "duration": "60",
            "capacity": "10",
            "level": "Beginner",
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "youtube_url": "https://youtu.be/abc123",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "/manage-courses" in resp.headers["Location"]


def test_take_course_requires_enrollment(client, monkeypatch, employee_user):
    with client.session_transaction() as sess:
        sess["employee"] = employee_user

    course = {"id": 1, "title": "C1", "youtube_url": "https://youtu.be/abc123"}

    def fake_api_get(path):
        if path == "courses/1":
            return course
        if path == "enrollments":
            return []  # no enrollment
        return []

    monkeypatch.setattr(flask_app, "api_get", fake_api_get)

    resp = client.get("/course/1/take", follow_redirects=False)
    # Should redirect back to /courses
    assert resp.status_code == 302
    assert "/courses" in resp.headers["Location"]


def test_take_course_ok_when_enrolled(client, monkeypatch, employee_user):
    with client.session_transaction() as sess:
        sess["employee"] = employee_user

    course = {"id": 1, "title": "C1", "youtube_url": "https://youtu.be/abc123"}
    enrollment = {
        "id": 10,
        "employee": {"id": employee_user["id"]},
        "course": {"id": 1},
        "status": "active",
    }

    def fake_api_get(path):
        if path == "courses/1":
            return course
        if path == "enrollments":
            return [enrollment]
        return []

    monkeypatch.setattr(flask_app, "api_get", fake_api_get)

    resp = client.get("/course/1/take")
    assert resp.status_code == 200


def test_update_progress_unauthenticated(client):
    resp = client.post("/update-progress/1", json={"progress": 50})
    assert resp.status_code == 401


def test_update_progress_not_enrolled(client, monkeypatch, employee_user):
    with client.session_transaction() as sess:
        sess["employee"] = employee_user

    monkeypatch.setattr(flask_app, "api_get", lambda path: [])
    resp = client.post("/update-progress/1", json={"progress": 50})
    assert resp.status_code == 404


def test_update_progress_ok(client, monkeypatch, employee_user):
    with client.session_transaction() as sess:
        sess["employee"] = employee_user

    enrollment = {
        "id": 10,
        "employee": {"id": employee_user["id"]},
        "course": {"id": 1},
        "progress": 0,
    }

    def fake_api_get(path):
        if path == "enrollments":
            return [enrollment]
        return []

    mock_patch_resp = MagicMock()
    mock_patch_resp.status_code = 200

    monkeypatch.setattr(flask_app, "api_get", fake_api_get)
    monkeypatch.setattr(flask_app, "api_patch", lambda path, data: mock_patch_resp)

    resp = client.post("/update-progress/1", json={"progress": 80})
    assert resp.status_code == 200


def test_mark_completed_not_enrolled(client, monkeypatch, employee_user):
    with client.session_transaction() as sess:
        sess["employee"] = employee_user

    monkeypatch.setattr(flask_app, "api_get", lambda path: [])
    resp = client.post("/mark-completed/1", follow_redirects=False)
    assert resp.status_code == 302
    assert "/courses" in resp.headers["Location"]


def test_mark_completed_ok(client, monkeypatch, employee_user):
    with client.session_transaction() as sess:
        sess["employee"] = employee_user

    enrollment = {
        "id": 10,
        "employee": {"id": employee_user["id"]},
        "course": {"id": 1},
        "status": "active",
    }

    def fake_api_get(path):
        if path == "enrollments":
            return [enrollment]
        return []

    mock_resp = MagicMock()
    mock_resp.status_code = 200

    monkeypatch.setattr(flask_app, "api_get", fake_api_get)
    monkeypatch.setattr(flask_app, "api_patch", lambda path, data: mock_resp)

    resp = client.post("/mark-completed/1", follow_redirects=False)
    assert resp.status_code == 302
    assert "/courses" in resp.headers["Location"]
