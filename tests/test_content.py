import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_brand_repository
from app.main import app
from app.repositories.brand_repository import BrandRepository
from app.schemas.contracts import BrandProfile

_BRAND = BrandProfile(
    hospital_name="테스트 피부과",
    target_audience="30-40대 직장 여성",
    doctor_philosophy="과장 없는 솔직한 설명, 회복 기간 공유",
    signature_procedures=["피코토닝", "잡티케어"],
    brand_tone=["신뢰감", "친근함"],
    banned_terms=["완치", "100% 효과"],
)

_VALID_REQUEST = {
    "event_name": "봄 피부 이벤트",
    "event_start": "2026-04-01",
    "event_end": "2026-04-30",
    "core_message": "봄맞이 피부 관리를 전문의와 함께",
    "highlights": ["30% 할인", "무료 상담"],
    "channels": ["blog", "sns", "web", "app"],
}


@pytest.fixture()
def client_with_brand():
    """브랜드 프로필이 미리 저장된 TestClient."""
    repo = BrandRepository()
    repo.save(_BRAND)
    app.dependency_overrides[get_brand_repository] = lambda: repo
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def client_no_brand():
    """브랜드 프로필이 없는 TestClient."""
    repo = BrandRepository()
    app.dependency_overrides[get_brand_repository] = lambda: repo
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_generate_all_channels(client_with_brand: TestClient) -> None:
    response = client_with_brand.post("/api/content/generate", json=_VALID_REQUEST)
    assert response.status_code == 200
    body = response.json()
    assert body["event_name"] == "봄 피부 이벤트"
    assert set(body["channels"].keys()) == {"blog", "sns", "web", "app"}
    assert len(body["review_notes"]) > 0


def test_generate_channel_fields(client_with_brand: TestClient) -> None:
    response = client_with_brand.post("/api/content/generate", json=_VALID_REQUEST)
    for channel, draft in response.json()["channels"].items():
        assert "headline" in draft, f"{channel} missing headline"
        assert "body" in draft, f"{channel} missing body"
        assert "cta" in draft, f"{channel} missing cta"
        assert draft["headline"], f"{channel} headline is empty"


def test_generate_single_channel(client_with_brand: TestClient) -> None:
    request = {**_VALID_REQUEST, "channels": ["sns"]}
    response = client_with_brand.post("/api/content/generate", json=request)
    assert response.status_code == 200
    assert list(response.json()["channels"].keys()) == ["sns"]


def test_generate_hospital_name_in_content(client_with_brand: TestClient) -> None:
    response = client_with_brand.post("/api/content/generate", json=_VALID_REQUEST)
    blog = response.json()["channels"]["blog"]
    assert "테스트 피부과" in blog["headline"]


def test_generate_without_brand_profile(client_no_brand: TestClient) -> None:
    response = client_no_brand.post("/api/content/generate", json=_VALID_REQUEST)
    assert response.status_code == 422


def test_generate_empty_channels(client_with_brand: TestClient) -> None:
    request = {**_VALID_REQUEST, "channels": []}
    response = client_with_brand.post("/api/content/generate", json=request)
    assert response.status_code == 422