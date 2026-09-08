from tests.conftest import RESUME_TEXT, auth_headers, client


def test_register_new_user():
    resp = client.post(
        "/api/auth/register",
        json={
            "username": "newbie",
            "email": "newbie@example.com",
            "password": "password123",
            "full_name": "New User",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["access_token"]
    assert data["user"]["email"] == "newbie@example.com"


def test_register_duplicate_email_conflicts():
    resp = client.post(
        "/api/auth/register",
        json={
            "username": "copycat",
            "email": "newbie@example.com",
            "password": "password123",
            "full_name": "Copy Cat",
        },
    )
    assert resp.status_code == 409


def test_register_short_password_fails():
    resp = client.post(
        "/api/auth/register",
        json={
            "username": "shorty",
            "email": "shorty@example.com",
            "password": "123",
            "full_name": "Short Password",
        },
    )
    assert resp.status_code == 422


def test_login_success():
    resp = client.post(
        "/api/auth/login",
        json={"email": "newbie@example.com", "password": "password123"},
    )
    assert resp.status_code == 200
    assert resp.json()["token_type"] == "bearer"


def test_login_wrong_password_fails():
    resp = client.post(
        "/api/auth/login",
        json={"email": "newbie@example.com", "password": "wrongpass"},
    )
    assert resp.status_code == 401


def test_login_missing_user_fails():
    resp = client.post(
        "/api/auth/login",
        json={"email": "ghost@example.com", "password": "whatever1"},
    )
    assert resp.status_code == 401


def test_me_endpoint_returns_user():
    resp = client.get("/api/auth/me", headers=auth_headers())
    assert resp.status_code == 200
    assert resp.json()["email"] == "testuser@example.com"


def test_me_without_token_fails():
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_me_with_bad_token_fails():
    resp = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-token"})
    assert resp.status_code == 401