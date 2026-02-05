"""Tests for company/product master data APIs and normalization."""

from fastapi.testclient import TestClient

from app.main import app
from app.services.normalization import normalize_company_name, normalize_product_name


def test_normalize_company_name() -> None:
    assert normalize_company_name("株式会社テスト") == "テスト"
    assert normalize_company_name("Test Inc.") == "test"
    assert normalize_company_name("(株)サンプル") == "サンプル"


def test_normalize_product_name() -> None:
    assert normalize_product_name("Model-X 200") == "modelx200"
    assert normalize_product_name("ＡＢＣ　１２３") == "abc123"


def test_company_create_and_search() -> None:
    client = TestClient(app)
    response = client.post(
        "/v1/companies",
        json={
            "name": "株式会社テスト",
            "corporate_number": "1234567890123",
            "aliases": ["テスト", "Test Inc."],
        },
    )
    assert response.status_code == 200
    company_id = response.json()["company_id"]
    assert company_id

    search_response = client.get("/v1/companies/search", params={"q": "Test"})
    assert search_response.status_code == 200
    results = search_response.json()["results"]
    assert any(item["company_id"] == company_id for item in results)


def test_company_create_rejects_invalid_corporate_number() -> None:
    client = TestClient(app)
    response = client.post(
        "/v1/companies",
        json={"name": "株式会社エラー", "corporate_number": "1234"},
    )
    assert response.status_code == 400


def test_product_create_and_search() -> None:
    client = TestClient(app)
    company_response = client.post(
        "/v1/companies",
        json={"name": "株式会社プロダクト", "corporate_number": "9876543210987"},
    )
    company_id = company_response.json()["company_id"]

    product_response = client.post(
        "/v1/products",
        json={
            "company_id": company_id,
            "name": "テスト装置",
            "model_number": "X-100",
        },
    )
    assert product_response.status_code == 200
    product_id = product_response.json()["product_id"]
    assert product_id

    search_response = client.get("/v1/products/search", params={"q": "X-100"})
    assert search_response.status_code == 200
    results = search_response.json()["results"]
    assert any(item["product_id"] == product_id for item in results)
