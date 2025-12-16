from unittest.mock import MagicMock
import app as flask_app


def test_index_route(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Rendered Index.html" in resp.data


def test_register_get(client):
    resp = client.get("/register")
    assert resp.status_code == 200


def test_register_post_success(client, monkeypatch):
    mock_resp = MagicMock()
    mock_resp.status_code = 201
    mock_resp.json.return_value = {"id": 1, "admin": False, "department": "IT"}

    monkeypatch.setattr(flask_app, "api_post", lambda path, data, files=None: mock_resp)

    resp = client.post(
        "/register",
        data={
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "position": "Dev",
            "department": "IT",
            "phone": "123",
            "hire_date": "2024-01-01",
            "gender": "male",
        },
        follow_redirects=False,
    )

    assert resp.status_code == 302
    assert "/dashboard" in resp.headers["Location"]


def test_register_post_fail(client, monkeypatch):
    mock_resp = MagicMock()
    mock_resp.status_code = 400

    monkeypatch.setattr(flask_app, "api_post", lambda path, data, files=None: mock_resp)

    resp = client.post(
        "/register",
        data={
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "position": "Dev",
            "department": "IT",
            "phone": "123",
            "hire_date": "2024-01-01",
            "gender": "male",
        },
    )

    # It should re-render form (200) rather than redirect
    assert resp.status_code == 200


def test_login_get(client):
    resp = client.get("/login")
    assert resp.status_code == 200


def test_login_employee_success(client, monkeypatch, employee_user):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = employee_user

    def fake_post(url, json=None):
        return mock_resp

    monkeypatch.setattr(flask_app.requests, "post", fake_post)

    resp = client.post(
        "/login",
        data={"email": employee_user["email"], "hire_date": "2024-01-01"},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "/dashboard" in resp.headers["Location"]


def test_login_admin_success(client, monkeypatch, admin_user):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = admin_user

    monkeypatch.setattr(flask_app.requests, "post", lambda url, json=None: mock_resp)

    resp = client.post(
        "/login",
        data={"email": admin_user["email"], "hire_date": "2024-01-01"},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "/admin-dashboard" in resp.headers["Location"]


def test_login_failure(client, monkeypatch):
    mock_resp = MagicMock()
    mock_resp.status_code = 401

    monkeypatch.setattr(flask_app.requests, "post", lambda url, json=None: mock_resp)

    resp = client.post(
        "/login",
        data={"email": "wrong@example.com", "hire_date": "2024-01-01"},
    )
    assert resp.status_code == 200  # form re-rendered


def test_logout_clears_session(client, employee_user):
    # simulate logged-in
    with client.session_transaction() as sess:
        sess["employee"] = employee_user

    resp = client.get("/logout", follow_redirects=False)
    assert resp.status_code == 302
    assert "/" in resp.headers["Location"]

    with client.session_transaction() as sess:
        assert "employee" not in sess
