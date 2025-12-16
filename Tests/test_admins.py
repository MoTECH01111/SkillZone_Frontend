from unittest.mock import MagicMock
import app as flask_app


def test_manage_employees_requires_admin(client):
    resp = client.get("/manage_employees", follow_redirects=False)
    assert resp.status_code == 302
    assert "/dashboard" in resp.headers["Location"]


def test_manage_employees_ok(client, monkeypatch, admin_user):
    with client.session_transaction() as sess:
        sess["employee"] = admin_user

    def fake_api_get(path):
        if path == "employees":
            return []
        if path == "enrollments":
            return []
        return []

    monkeypatch.setattr(flask_app, "api_get", fake_api_get)

    resp = client.get("/manage_employees")
    assert resp.status_code == 200


def test_admin_create_employee(client, monkeypatch, admin_user):
    with client.session_transaction() as sess:
        sess["employee"] = admin_user

    mock_resp = MagicMock()
    mock_resp.status_code = 201

    monkeypatch.setattr(flask_app, "api_post", lambda path, data: mock_resp)

    resp = client.post(
        "/admin/create-employee",
        data={
            "first_name": "New",
            "last_name": "Emp",
            "email": "new@example.com",
            "position": "Dev",
            "department": "IT",
            "phone": "123",
            "hire_date": "2024-01-01",
            "gender": "male",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "/manage_employees" in resp.headers["Location"]


def test_edit_employee(client, monkeypatch, admin_user):
    with client.session_transaction() as sess:
        sess["employee"] = admin_user

    mock_resp = MagicMock()
    mock_resp.status_code = 200

    monkeypatch.setattr(flask_app, "api_patch", lambda path, data: mock_resp)

    resp = client.post(
        "/edit-employee/1",
        data={
            "first_name": "Updated",
            "last_name": "Emp",
            "email": "new@example.com",
            "position": "Dev",
            "department": "IT",
            "phone": "123",
            "hire_date": "2024-01-01",
            "gender": "male",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "/manage_employees" in resp.headers["Location"]


def test_delete_employee(client, monkeypatch, admin_user):
    with client.session_transaction() as sess:
        sess["employee"] = admin_user

    mock_resp = MagicMock()
    mock_resp.status_code = 204
    monkeypatch.setattr(flask_app, "api_delete", lambda path: mock_resp)

    resp = client.post("/employee/delete/1", follow_redirects=False)
    assert resp.status_code == 302
    assert "/manage_employees" in resp.headers["Location"]


def test_admin_enrollments_view(client, monkeypatch, admin_user):
    with client.session_transaction() as sess:
        sess["employee"] = admin_user

    monkeypatch.setattr(flask_app, "api_get", lambda path: [])

    resp = client.get("/admin/enrollments")
    assert resp.status_code == 200


def test_unenroll(client, monkeypatch, admin_user):
    with client.session_transaction() as sess:
        sess["employee"] = admin_user

    mock_resp = MagicMock()
    mock_resp.status_code = 204

    monkeypatch.setattr(flask_app, "api_delete", lambda path: mock_resp)

    resp = client.post("/unenroll/1", follow_redirects=False)
    assert resp.status_code == 302
    assert "/admin/enrollments" in resp.headers["Location"]


def test_edit_course(client, monkeypatch, admin_user):
    with client.session_transaction() as sess:
        sess["employee"] = admin_user

    mock_resp = MagicMock()
    mock_resp.status_code = 200

    monkeypatch.setattr(flask_app, "api_patch", lambda path, data: mock_resp)

    resp = client.post(
        "/course/edit/1",
        data={
            "title": "Updated",
            "description": "Desc",
            "duration": "60",
            "capacity": "10",
            "level": "Intermediate",
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "youtube_url": "https://youtu.be/abc123",
            "department": "IT",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "/manage-courses" in resp.headers["Location"]


def test_delete_course(client, monkeypatch, admin_user):
    with client.session_transaction() as sess:
        sess["employee"] = admin_user

    mock_resp = MagicMock()
    mock_resp.status_code = 204

    monkeypatch.setattr(flask_app, "api_delete", lambda path: mock_resp)

    resp = client.post("/course/delete/1", follow_redirects=False)
    assert resp.status_code == 302
    assert "/manage-courses" in resp.headers["Location"]
