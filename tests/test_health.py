from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_root() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "running"


def test_simulation_preview() -> None:
    response = client.post(
        "/api/simulation/preview",
        json={
            "promotion_name": "봄 이벤트",
            "promo_price": 149000,
            "list_price": 220000,
            "procedure_cost": 42000,
            "expected_leads": 30,
            "close_rate": 0.4,
            "upsell_rate": 0.2,
            "average_upsell_revenue": 80000,
            "repeat_visit_rate": 0.1,
            "repeat_visit_revenue": 100000,
            "ad_budget": 1000000,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["promotion_name"] == "봄 이벤트"
    assert payload["expected_patients"] == 12.0
    assert "projected_profit" in payload
    assert "break_even_patients" in payload
    assert "allowed_ad_budget" in payload
    assert isinstance(payload["breakeven_reached"], bool)


def test_simulation_invalid_price() -> None:
    response = client.post(
        "/api/simulation/preview",
        json={
            "promotion_name": "테스트",
            "promo_price": -1,  # invalid
            "list_price": 100000,
            "procedure_cost": 0,
            "expected_leads": 10,
            "close_rate": 0.5,
            "upsell_rate": 0,
            "average_upsell_revenue": 0,
            "repeat_visit_rate": 0,
            "repeat_visit_revenue": 0,
            "ad_budget": 0,
        },
    )
    assert response.status_code == 422


def test_review_checklist() -> None:
    response = client.get("/api/review/checklist")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 5
    stages = [item["stage"] for item in items]
    assert "브랜드 톤 검토" in stages
    assert "최종 원장 승인" in stages