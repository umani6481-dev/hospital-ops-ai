def _register_and_login(client, email, role="staff"):
    client.post("/api/auth/register", json={
        "full_name": "User", "email": email, "password": "Pass123!", "role": role,
    })
    res = client.post("/api/auth/login", json={"email": email, "password": "Pass123!"})
    return res.json()["access_token"]


def test_staff_cannot_create_department(client):
    token = _register_and_login(client, "staff.rbac@example.com", role="staff")
    res = client.post(
        "/api/departments",
        json={"hospital_id": "x", "name": "Test Dept"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403


def test_admin_can_create_department(client):
    token = _register_and_login(client, "admin.rbac@example.com", role="admin")
    res = client.post(
        "/api/departments",
        json={"hospital_id": "hosp-1", "name": "Test Dept", "capacity": 40},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    assert res.json()["name"] == "Test Dept"


def test_patient_crud(client):
    token = _register_and_login(client, "patient.crud@example.com", role="staff")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post("/api/patients", json={"age_group": "19-35", "gender": "Female", "region": "North"}, headers=headers)
    assert res.status_code == 201
    patient_id = res.json()["id"]

    res = client.get(f"/api/patients/{patient_id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["region"] == "North"


def test_invalid_role_rejected(client):
    res = client.post("/api/auth/register", json={
        "full_name": "Bad Role", "email": "badrole@example.com", "password": "Pass123!", "role": "superuser",
    })
    assert res.status_code == 400
