import io
import uuid

from fastapi.testclient import TestClient

from app.main import app


def auth(client: TestClient, email: str = "analyst@asteria.demo", password: str = "Analyst123!") -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_health_and_readiness() -> None:
    with TestClient(app) as client:
        assert client.get("/api/v1/health").json()["status"] == "healthy"
        assert client.get("/api/v1/readiness").status_code == 200


def test_login_rejects_bad_password() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "analyst@asteria.demo", "password": "bad"},
        )
        assert response.status_code == 401


def test_upload_profile_analyse_and_export() -> None:
    with TestClient(app) as client:
        headers = auth(client)
        unique_revenue = uuid.uuid4().int % 1_000_000_000
        content = f"region,revenue\nNorth,10\nSouth,30\nNorth,{unique_revenue}\n".encode()
        uploaded = client.post(
            "/api/v1/data-sources/upload",
            headers=headers,
            files={
                "file": (
                    f"orders-{uuid.uuid4()}.csv",
                    io.BytesIO(content),
                    "text/csv",
                )
            },
        )
        assert uploaded.status_code == 201, uploaded.text
        source = uploaded.json()
        assert source["row_count"] == 3
        profile = client.get(f"/api/v1/data-sources/{source['id']}/profile", headers=headers)
        assert profile.json()["column_count"] == 2
        result = client.post(
            "/api/v1/analysis/run",
            headers=headers,
            json={"question": "Revenue by region", "data_source_id": source["id"]},
        )
        assert result.status_code == 200, result.text
        payload = result.json()
        assert payload["response_type"] == "analysis_result"
        assert payload["plan"]["recommended_chart"] == "bar"
        exported = client.get(
            f"/api/v1/analyses/{payload['analysis_id']}/export.csv",
            headers=headers,
        )
        assert exported.status_code == 200
        assert "region" in exported.text


def test_authentication_is_required() -> None:
    with TestClient(app) as client:
        assert client.get("/api/v1/data-sources").status_code == 401


def test_admin_metrics_are_role_protected() -> None:
    with TestClient(app) as client:
        assert client.get("/api/v1/admin/metrics", headers=auth(client)).status_code == 403
        admin = auth(client, "admin@asteria.demo", "Admin123!")
        assert client.get("/api/v1/admin/metrics", headers=admin).status_code == 200
