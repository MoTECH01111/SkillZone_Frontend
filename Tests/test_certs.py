from io import BytesIO
from unittest.mock import MagicMock
import app as flask_app


def test_admin_certificates_view(client, monkeypatch, admin_user):
    with client.session_transaction() as sess:
        sess["employee"] = admin_user

    def fake_api_get(path):
        if path == "courses":
            return []
        if path == "certificates":
            return []
        return []

    monkeypatch.setattr(flask_app, "api_get", fake_api_get)

    resp = client.get("/admin/certificates")
    assert resp.status_code == 200


def test_update_certificate_no_logo(client, monkeypatch, admin_user):
    with client.session_transaction() as sess:
        sess["employee"] = admin_user

    mock_resp = MagicMock()
    mock_resp.status_code = 200

    monkeypatch.setattr(flask_app, "api_patch", lambda path, data: mock_resp)

    resp = client.post(
        "/certificate/update/1",
        data={
            "name": "Cert Name",
            "description": "Desc",
            "issued_on": "2024-01-01",
            "expiry_date": "2025-01-01",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "/admin/certificates" in resp.headers["Location"]


def test_delete_certificate(client, monkeypatch, admin_user):
    with client.session_transaction() as sess:
        sess["employee"] = admin_user

    mock_resp = MagicMock()
    mock_resp.status_code = 204

    monkeypatch.setattr(flask_app, "api_delete", lambda path: mock_resp)

    resp = client.post("/certificate/delete/1", follow_redirects=False)
    assert resp.status_code == 302
    assert "/admin/certificates" in resp.headers["Location"]


def test_create_certificate_success(client, monkeypatch, admin_user):
    """
    This actually runs the PDF generation but mocks the API call to Rails.
    """
    with client.session_transaction() as sess:
        sess["employee"] = admin_user

    mock_resp = MagicMock()
    mock_resp.status_code = 201

    monkeypatch.setattr(flask_app, "api_post", lambda path, data, files=None: mock_resp)

    data = {
        "name": "Test Cert",
        "description": "A test cert",
        "issued_on": "2024-01-01",
        "expiry_date": "2025-01-01",
        "course_id": "1",
        "employee_id": "1",
    }

    # Send a fake logo file.
    logo_file = (BytesIO(b"fake image data"), "logo.png")

    resp = client.post(
        "/admin/certificates/create",
        data={**data, "logo": logo_file},
        content_type="multipart/form-data",
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "/admin/certificates" in resp.headers["Location"]
