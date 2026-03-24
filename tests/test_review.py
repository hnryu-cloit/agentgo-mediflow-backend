import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_review_repository
from app.main import app
from app.repositories.review_repository import ReviewRepository


@pytest.fixture()
def client():
    """매 테스트마다 독립된 ReviewRepository를 사용하는 TestClient."""
    repo = ReviewRepository()
    app.dependency_overrides[get_review_repository] = lambda: repo
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_checklist_returns_five_items(client: TestClient) -> None:
    response = client.get("/api/review/checklist")
    assert response.status_code == 200
    assert len(response.json()) == 5


def test_checklist_initial_status_pending(client: TestClient) -> None:
    items = client.get("/api/review/checklist").json()
    for item in items:
        assert item["status"] == "pending"


def test_update_status_approved(client: TestClient) -> None:
    response = client.patch(
        "/api/review/브랜드 톤 검토",
        json={"status": "approved"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "approved"
    assert response.json()["stage"] == "브랜드 톤 검토"


def test_update_status_with_notes(client: TestClient) -> None:
    response = client.patch(
        "/api/review/금지어 포함 여부",
        json={"status": "rejected", "notes": "완치 표현 발견"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "rejected"
    assert body["notes"] == "완치 표현 발견"


def test_update_invalid_status(client: TestClient) -> None:
    response = client.patch(
        "/api/review/브랜드 톤 검토",
        json={"status": "invalid_status"},
    )
    assert response.status_code == 422


def test_update_nonexistent_stage(client: TestClient) -> None:
    response = client.patch(
        "/api/review/존재하지 않는 단계",
        json={"status": "approved"},
    )
    assert response.status_code == 404


def test_update_reflects_in_checklist(client: TestClient) -> None:
    client.patch("/api/review/최종 원장 승인", json={"status": "approved"})
    items = client.get("/api/review/checklist").json()
    final = next(i for i in items if i["stage"] == "최종 원장 승인")
    assert final["status"] == "approved"


def test_all_valid_statuses(client: TestClient) -> None:
    for status in ("pending", "in_review", "approved", "rejected"):
        response = client.patch(
            "/api/review/가격 정보 정확성",
            json={"status": status},
        )
        assert response.status_code == 200, f"status={status} failed"