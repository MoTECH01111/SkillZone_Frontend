from unittest.mock import MagicMock
import app as flask_app


def test_dashboard_requires_login(client):
    resp = client.get("/dashboard", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_dashboard_employee_view(client, monkeypatch, employee_user):
    # Mock session
    with client.session_transaction() as sess:
        sess["employee"] = employee_user

    # Fake enrollments and certificates
    enrollments = [
        {
            "id": 1,
            "employee": {"id": employee_user["id"]},
            "course": {"id": 10, "title": "Course A"},
            "status": "completed",
        },
        {
            "id": 2,
            "employee": {"id": 999},
            "course": {"id": 20, "title": "Other's course"},
            "status": "active",
        },
    ]

    certificates = [
        {"id": 5, "course": {"id": 10, "title": "Course A"}},
        {"id": 6, "course": {"id": 999, "title": "Other"}},
    ]

    def fake_api_get(path):
        if path == "enrollments":
            return enrollments
        if path == "certificates":
            return certificates
        return []

    monkeypatch.setattr(flask_app, "api_get", fake_api_get)

    resp = client.get("/dashboard")
    assert resp.status_code == 200
    # We mainly care that it renders without error and used the right template
    assert b"Dashboard.html" in resp.data or b"Rendered Dashboard.html" in resp.data


def test_employee_profile_get(client, employee_user):
    with client.session_transaction() as sess:
        sess["employee"] = employee_user

    resp = client.get("/employee/profile")
    assert resp.status_code == 200


def test_employee_profile_post_update_success(client, monkeypatch, employee_user):
    with client.session_transaction() as sess:
        sess["employee"] = employee_user

    updated_employee = employee_user.copy()
    updated_employee["first_name"] = "Updated"

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = updated_employee

    monkeypatch.setattr(
        flask_app, "api_patch", lambda path, data: mock_resp
    )

    resp = client.post(
        "/employee/profile",
        data={
            "first_name": "Updated",
            "last_name": "User",
            "email": "emp@example.com",
            "position": "Dev",
            "department": "IT",
            "phone": "123",
            "gender": "Male",
        },
        follow_redirects=False,
    )

    assert resp.status_code == 302
    assert "/employee/profile" in resp.headers["Location"]


def test_admin_dashboard_requires_admin(client):
    resp = client.get("/admin-dashboard", follow_redirects=False)
    # Not logged in redirected to /dashboard which then redirects to /login
    assert resp.status_code == 302
    assert "/dashboard" in resp.headers["Location"]


def test_admin_dashboard_ok(client, monkeypatch, admin_user):
    with client.session_transaction() as sess:
        sess["employee"] = admin_user

    def fake_api_get(path):
        if path == "employees":
            return []
        if path == "courses":
            return []
        if path == "enrollments":
            return []
        if path == "certificates":
            return []
        return []

    monkeypatch.setattr(flask_app, "api_get", fake_api_get)

    resp = client.get("/admin-dashboard")
    assert resp.status_code == 200
