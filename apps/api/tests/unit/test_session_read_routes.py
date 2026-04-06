"""Read routes: list sessions, get session, list/get artifacts (mocked DB)."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.db.models import Artifact, DesignSession
from app.db.session import get_db
from app.main import app


@pytest.fixture
def client_and_db() -> tuple[TestClient, MagicMock]:
    db = MagicMock()

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client, db
    app.dependency_overrides.clear()


def test_list_sessions_empty(client_and_db: tuple[TestClient, MagicMock]) -> None:
    client, db = client_and_db
    m_result = MagicMock()
    m_result.all.return_value = []
    db.scalars.return_value = m_result

    r = client.get("/api/v1/sessions")
    assert r.status_code == 200
    body = r.json()
    assert "data" in body and "meta" in body
    assert body["data"]["sessions"] == []


def test_list_sessions_one_row(client_and_db: tuple[TestClient, MagicMock]) -> None:
    client, db = client_and_db
    sid = uuid4()
    ts = datetime(2026, 4, 1, 12, 0, 0, tzinfo=UTC)
    row = MagicMock()
    row.id = sid
    row.title = "My session"
    row.phase = "product"
    row.updated_at = ts
    m_result = MagicMock()
    m_result.all.return_value = [row]
    db.scalars.return_value = m_result

    r = client.get("/api/v1/sessions")
    assert r.status_code == 200
    sess = r.json()["data"]["sessions"][0]
    assert sess["id"] == str(sid)
    assert sess["title"] == "My session"
    assert sess["phase"] == "product"
    assert "updated_at" in sess


def test_get_session_404(client_and_db: tuple[TestClient, MagicMock]) -> None:
    client, db = client_and_db
    db.get.return_value = None

    r = client.get(f"/api/v1/sessions/{uuid4()}")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "session_not_found"


def test_list_artifacts_empty(client_and_db: tuple[TestClient, MagicMock]) -> None:
    client, db = client_and_db
    sid = uuid4()
    session_row = MagicMock()
    db.get.return_value = session_row
    m_result = MagicMock()
    m_result.all.return_value = []
    db.scalars.return_value = m_result

    r = client.get(f"/api/v1/sessions/{sid}/artifacts")
    assert r.status_code == 200
    assert r.json()["data"]["artifacts"] == []


def test_get_artifact_wrong_session(client_and_db: tuple[TestClient, MagicMock]) -> None:
    client, db = client_and_db
    sid = uuid4()
    aid = uuid4()
    session_row = MagicMock()
    art = MagicMock()
    art.session_id = uuid4()  # different from sid

    def getter(model: type, pk):  # noqa: ANN401
        if model is DesignSession:
            return session_row if pk == sid else None
        if model is Artifact:
            return art if pk == aid else None
        return None

    db.get.side_effect = getter

    r = client.get(f"/api/v1/sessions/{sid}/artifacts/{aid}")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "artifact_not_found"
