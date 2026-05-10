from fastapi.testclient import TestClient

from app.main import app


def test_checklist_returns_five_items() -> None:
    with TestClient(app) as client:
        response = client.get("/api/review/checklist")
        assert response.status_code == 200
        assert len(response.json()) == 5


def test_update_review_status_by_id() -> None:
    with TestClient(app) as client:
        items = client.get("/api/review/checklist").json()
        item_id = items[0]["id"]

        response = client.patch(
            f"/api/review/{item_id}",
            json={"status": "approved", "notes": "확인 완료"},
            headers={"X-User-Role": "marketing_manager"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "approved"


def test_invalid_review_status_rejected() -> None:
    with TestClient(app) as client:
        items = client.get("/api/review/checklist").json()
        response = client.patch(
            f"/api/review/{items[0]['id']}",
            json={"status": "invalid"},
            headers={"X-User-Role": "staff"},
        )
        assert response.status_code == 422
