from datetime import timedelta


# ── Helpers ───────────────────────────────────────────────────────────────────

def register(client, email="test@example.com", password="password123"):
    return client.post("/api/v1/auth/register", json={"email": email, "password": password})


def login(client, email="test@example.com", password="password123"):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


# ── Registration ──────────────────────────────────────────────────────────────

def test_register_success(client):
    res = register(client, "newuser@example.com")
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 20


def test_register_duplicate_email(client):
    register(client, "dup@example.com")
    res = register(client, "dup@example.com")
    assert res.status_code == 409


def test_register_invalid_email(client):
    res = client.post(
        "/api/v1/auth/register",
        json={"email": "not-an-email", "password": "password123"},
    )
    assert res.status_code == 422


def test_register_short_password(client):
    res = register(client, "short@example.com", "abc")
    assert res.status_code == 422


def test_register_password_not_returned(client):
    res = register(client, "safe@example.com")
    body = res.json()
    assert "password" not in body
    assert "password_hash" not in body


# ── Login ─────────────────────────────────────────────────────────────────────

def test_login_success(client):
    register(client, "loginok@example.com")
    res = login(client, "loginok@example.com")
    assert res.status_code == 200
    assert "access_token" in res.json()


def test_login_wrong_password(client):
    register(client, "wrongpw@example.com")
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "wrongpw@example.com", "password": "wrongpassword"},
    )
    assert res.status_code == 401


def test_login_unknown_email(client):
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "ghost@example.com", "password": "password123"},
    )
    assert res.status_code == 401


def test_login_generic_error_message(client):
    """Wrong password and unknown email must return identical 401 (no user enumeration)."""
    r1 = client.post(
        "/api/v1/auth/login",
        json={"email": "ghost2@example.com", "password": "password123"},
    )
    register(client, "real2@example.com")
    r2 = client.post(
        "/api/v1/auth/login",
        json={"email": "real2@example.com", "password": "wrongpassword"},
    )
    assert r1.status_code == 401
    assert r2.status_code == 401
    # Both return same detail string — no enumeration
    assert r1.json()["detail"] == r2.json()["detail"]


# ── JWT / Protected endpoints ─────────────────────────────────────────────────

def test_missing_token_returns_403(client):
    """HTTPBearer returns 403 when Authorization header is absent."""
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 403


def test_invalid_token_returns_401(client):
    res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer this.is.not.valid"},
    )
    assert res.status_code == 401


def test_expired_token_returns_401(client):
    from app.utils.jwt_utils import create_access_token
    expired = create_access_token(
        data={"sub": "00000000-0000-0000-0000-000000000001"},
        expires_delta=timedelta(seconds=-1),
    )
    res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired}"},
    )
    assert res.status_code == 401


def test_get_me_success(client):
    res = register(client, "me@example.com")
    token = res.json()["access_token"]
    me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me.status_code == 200
    data = me.json()
    assert data["email"] == "me@example.com"
    assert "id" in data
    assert "created_at" in data


def test_get_me_no_password_hash(client):
    res = register(client, "nohash@example.com")
    token = res.json()["access_token"]
    me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    data = me.json()
    assert "password_hash" not in data
    assert "password" not in data


def test_protected_route_rejects_no_token(client):
    """Any endpoint using get_current_user must reject requests with no token."""
    res = client.get("/api/v1/auth/me")
    assert res.status_code in (401, 403)
