import uuid

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models import AnalysisRun, Conversation, DataSource, User
from app.db.session import SessionLocal
from app.main import app


def login(client: TestClient, email: str, password: str) -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_user_cannot_save_another_users_analysis() -> None:
    with TestClient(app) as client, SessionLocal() as db:
        analyst = db.scalar(select(User).where(User.email == "analyst@asteria.demo"))
        assert analyst is not None
        source = DataSource(
            owner_id=analyst.id,
            name=f"ownership-{uuid.uuid4()}",
            status="ready",
        )
        db.add(source)
        db.flush()
        conversation = Conversation(
            user_id=analyst.id,
            title="Private analysis",
            data_source_id=source.id,
        )
        db.add(conversation)
        db.flush()
        run = AnalysisRun(
            conversation_id=conversation.id,
            user_question="Private question",
            analysis_plan={},
            query_type="dataframe_dsl",
            generated_query="{}",
            status="succeeded",
        )
        db.add(run)
        db.commit()
        admin_headers = login(client, "admin@asteria.demo", "Admin123!")
        response = client.post(
            "/api/v1/saved-analyses",
            headers=admin_headers,
            json={"analysis_run_id": run.id, "title": "Should be blocked"},
        )
        assert response.status_code == 404
