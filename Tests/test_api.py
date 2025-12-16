from unittest.mock import MagicMock
import app as flask_app


def test_api_get_success_dict(monkeypatch):
    def fake_get_current_employee():
        return {"id": 1}

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"foo": "bar"}

    monkeypatch.setattr(flask_app, "get_current_employee", fake_get_current_employee)
    monkeypatch.setattr(flask_app.requests, "get", lambda url, params=None: mock_resp)

    result = flask_app.api_get("something")
    assert result == {"foo": "bar"}


def test_api_get_success_string_json(monkeypatch):
    def fake_get_current_employee():
        return {"id": 1}

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = '{"hello": "world"}'

    monkeypatch.setattr(flask_app, "get_current_employee", fake_get_current_employee)
    monkeypatch.setattr(flask_app.requests, "get", lambda url, params=None: mock_resp)

    result = flask_app.api_get("something")
    assert result == {"hello": "world"}


def test_api_get_non_200(monkeypatch):
    mock_resp = MagicMock()
    mock_resp.status_code = 500

    monkeypatch.setattr(flask_app, "get_current_employee", lambda: {"id": 1})
    monkeypatch.setattr(flask_app.requests, "get", lambda url, params=None: mock_resp)

    result = flask_app.api_get("something")
    assert result is None


def test_api_get_exception(monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(flask_app, "get_current_employee", lambda: {"id": 1})
    monkeypatch.setattr(flask_app.requests, "get", boom)

    result = flask_app.api_get("something")
    assert result is None


def test_api_post_json(monkeypatch):
    mock_resp = MagicMock()
    mock_resp.status_code = 201

    def fake_post(url, params=None, json=None, data=None, files=None):
        assert "employee_id" in params
        assert json == {"foo": "bar"}
        return mock_resp

    monkeypatch.setattr(flask_app, "get_current_employee", lambda: {"id": 1})
    monkeypatch.setattr(flask_app.requests, "post", fake_post)

    resp = flask_app.api_post("path", {"foo": "bar"})
    assert resp.status_code == 201


def test_api_post_files(monkeypatch):
    mock_resp = MagicMock()
    mock_resp.status_code = 201

    def fake_post(url, params=None, json=None, data=None, files=None):
        assert data == {"field": "value"}
        assert "file" in files
        return mock_resp

    monkeypatch.setattr(flask_app, "get_current_employee", lambda: {"id": 1})
    monkeypatch.setattr(flask_app.requests, "post", fake_post)

    resp = flask_app.api_post("path", {"field": "value"}, files={"file": b"123"})
    assert resp.status_code == 201


def test_api_patch(monkeypatch):
    mock_resp = MagicMock()
    mock_resp.status_code = 200

    def fake_patch(url, params=None, json=None):
        assert json == {"update": "yes"}
        return mock_resp

    monkeypatch.setattr(flask_app, "get_current_employee", lambda: {"id": 1})
    monkeypatch.setattr(flask_app.requests, "patch", fake_patch)

    resp = flask_app.api_patch("path", {"update": "yes"})
    assert resp.status_code == 200


def test_api_delete(monkeypatch):
    mock_resp = MagicMock()
    mock_resp.status_code = 204

    def fake_delete(url, params=None):
        return mock_resp

    monkeypatch.setattr(flask_app, "get_current_employee", lambda: {"id": 1})
    monkeypatch.setattr(flask_app.requests, "delete", fake_delete)

    resp = flask_app.api_delete("path")
    assert resp.status_code == 204
