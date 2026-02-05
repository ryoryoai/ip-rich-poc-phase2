"""Tests for JP Index API endpoints."""

from datetime import date
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.db.models import JpCase, JpNumberAlias, JpSearchDocument


@pytest.fixture
def client() -> TestClient:
    """Create test client."""
    return TestClient(app)


def _seed_case() -> str:
    with SessionLocal() as db:
        case = JpCase(
            application_number_raw="特願2020-123456",
            application_number_norm="JP2020123456",
            title="テスト発明",
            current_status="pending",
            last_update_date=date(2026, 2, 4),
        )
        db.add(case)
        db.flush()

        alias = JpNumberAlias(
            case_id=case.id,
            number_type="application",
            number_raw="特願2020-123456",
            number_norm="JP2020123456",
            country="JP",
            is_primary=True,
        )
        db.add(alias)

        search_doc = JpSearchDocument(
            case_id=case.id,
            title="テスト発明",
            abstract="サンプル要約",
            applicants_text="株式会社サンプル",
            classifications_text="G06F",
            status="pending",
        )
        db.add(search_doc)
        db.commit()

        return str(case.id)


def test_jp_index_resolve(client: TestClient) -> None:
    response = client.get("/v1/jp-index/resolve", params={"input": "特願2020-123456"})
    assert response.status_code == 200
    data = response.json()
    assert data["normalized"] == "JP2020123456"
    assert data["number_type"] == "application"


def test_jp_index_search_by_number(client: TestClient) -> None:
    _seed_case()
    response = client.get("/v1/jp-index/search", params={"number": "特願2020-123456"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1
