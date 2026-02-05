"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_returns_ok(self, client: TestClient) -> None:
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestResolveEndpoint:
    """Tests for patent number resolution endpoint."""

    def test_resolves_japanese_format(self, client: TestClient) -> None:
        response = client.get("/v1/patents/resolve", params={"input": "特許第1234567号"})
        assert response.status_code == 200
        data = response.json()
        assert data["country"] == "JP"
        assert data["doc_number"] == "1234567"
        assert data["kind"] == "B2"
        assert data["normalized"] == "JP1234567B2"

    def test_resolves_alphanumeric_format(self, client: TestClient) -> None:
        response = client.get("/v1/patents/resolve", params={"input": "JP7654321B2"})
        assert response.status_code == 200
        data = response.json()
        assert data["doc_number"] == "7654321"
        assert data["kind"] == "B2"

    def test_resolves_number_only(self, client: TestClient) -> None:
        response = client.get("/v1/patents/resolve", params={"input": "1234567"})
        assert response.status_code == 200
        data = response.json()
        assert data["normalized"] == "JP1234567B2"

    def test_resolves_application_format(self, client: TestClient) -> None:
        response = client.get("/v1/patents/resolve", params={"input": "特願2020-123456"})
        assert response.status_code == 200
        data = response.json()
        assert data["kind"] == "A"

    def test_returns_400_for_invalid_input(self, client: TestClient) -> None:
        response = client.get("/v1/patents/resolve", params={"input": "invalid"})
        assert response.status_code == 400


class TestClaimsEndpoint:
    """Tests for claims retrieval endpoint."""

    def test_returns_404_for_nonexistent_patent(self, client: TestClient) -> None:
        response = client.get("/v1/patents/JP9999999B2/claims/1")
        assert response.status_code == 404
