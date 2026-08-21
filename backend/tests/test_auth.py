def test_health_check(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_register_and_login(client):
    payload = {
        "full_name": "Test Admin",
        "email": "test.admin@example.com",
        "password": "TestPass123!",
        "role": "admin",
    }
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 201
    assert res.json()["email"] == payload["email"]

    res = client.post("/api/auth/login", json={"email": payload["email"], "password": payload["password"]})
    assert res.status_code == 200
    body = res.json()
    assert "access_token" in body
    assert "refresh_token" in body


def test_login_wrong_password_fails(client):
    client.post("/api/auth/register", json={
        "full_name": "User2", "email": "user2@example.com", "password": "Correct123!", "role": "staff",
    })
    res = client.post("/api/auth/login", json={"email": "user2@example.com", "password": "Wrong123!"})
    assert res.status_code == 401


def test_protected_route_requires_token(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401


def test_duplicate_registration_rejected(client):
    payload = {"full_name": "Dup", "email": "dup@example.com", "password": "Pass123!", "role": "staff"}
    r1 = client.post("/api/auth/register", json=payload)
    assert r1.status_code == 201
    r2 = client.post("/api/auth/register", json=payload)
    assert r2.status_code == 400
