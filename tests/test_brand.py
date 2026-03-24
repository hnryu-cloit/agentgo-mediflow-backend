import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_brand_repository
from app.main import app
from app.repositories.brand_repository import BrandRepository

_VALID_PROFILE = {
    "hospital_name": "테스트 피부과",
    "target_audience": "30-40대 직장 여성",
    "doctor_philosophy": "과장 없는 솔직한 설명, 회복 기간 공유",
    "signature_procedures": ["피코토닝", "잡티케어"],
    "brand_tone": ["신뢰감", "친근함"],
    "banned_terms": ["완치", "100% 효과"],
}


@pytest.fixture()
def client():
    """매 테스트마다 독립된 BrandRepository를 사용하는 TestClient."""
    repo = BrandRepository()
    app.dependency_overrides[get_brand_repository] = lambda: repo
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_save_brand_profile(client: TestClient) -> None:
    response = client.post("/api/brand", json=_VALID_PROFILE)
    assert response.status_code == 201
    body = response.json()
    assert body["hospital_name"] == "테스트 피부과"
    assert "피코토닝" in body["signature_procedures"]


def test_get_brand_profile_not_found(client: TestClient) -> None:
    response = client.get("/api/brand")
    assert response.status_code == 404


def test_get_brand_profile_after_save(client: TestClient) -> None:
    client.post("/api/brand", json=_VALID_PROFILE)
    response = client.get("/api/brand")
    assert response.status_code == 200
    assert response.json()["hospital_name"] == "테스트 피부과"


def test_save_overwrites_existing(client: TestClient) -> None:
    client.post("/api/brand", json=_VALID_PROFILE)
    updated = {**_VALID_PROFILE, "hospital_name": "새 병원"}
    client.post("/api/brand", json=updated)
    response = client.get("/api/brand")
    assert response.json()["hospital_name"] == "새 병원"


def test_save_brand_empty_hospital_name(client: TestClient) -> None:
    invalid = {**_VALID_PROFILE, "hospital_name": ""}
    response = client.post("/api/brand", json=invalid)
    assert response.status_code == 422


def test_save_brand_empty_procedures(client: TestClient) -> None:
    invalid = {**_VALID_PROFILE, "signature_procedures": []}
    response = client.post("/api/brand", json=invalid)
    assert response.status_code == 422