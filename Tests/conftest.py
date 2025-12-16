import pytest
import app as flask_app


def fake_render(template_name, **context):
    """
    Fake template renderer used during tests.
    Includes actual context values so tests can assert on them.
    """
    output = [f"Rendered {template_name}"]
    for key, value in context.items():
        output.append(f"{key}: {value}")
    return "\n".join(output)


@pytest.fixture
def app(monkeypatch):
    """
    Configure Flask for testing and replace render_template with a fake renderer.
    """
    flask_app.app.config["TESTING"] = True
    flask_app.app.config["WTF_CSRF_ENABLED"] = False
    flask_app.app.config["SECRET_KEY"] = "test_secret"

    # Patch render_template globally in your app
    monkeypatch.setattr(flask_app, "render_template", fake_render)

    return flask_app.app


@pytest.fixture
def client(app):
    """
    Flask test client using the patched app.
    """
    return app.test_client()


@pytest.fixture
def employee_user():
    return {
        "id": 1,
        "first_name": "Emp",
        "last_name": "User",
        "email": "emp@example.com",
        "admin": False,
        "department": "IT",
    }


@pytest.fixture
def admin_user():
    return {
        "id": 2,
        "first_name": "Admin",
        "last_name": "User",
        "email": "admin@example.com",
        "admin": True,
        "department": "IT",
    }
