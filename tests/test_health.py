from fastapi.testclient import TestClient

from app.main import app


def test_health() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_root() -> None:
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "running"


def test_simulation_preview() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/simulation/preview",
            json={
                "procedure_id": "proc_masseter_botox",
                "promo_price": 29000,
                "expected_leads": 30,
                "conversion_rate": 40,
                "ad_spend": 100000,
                "upsell_estimate": 0,
                "consumable_cost": 15000,
                "labor_cost": 5000,
                "promo_period_weeks": 4,
            },
            headers={"X-User-Role": "staff"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["expected_patients"] == 12.0
        assert "projected_profit" in payload
        assert "break_even_patients" in payload
        assert payload["promo_period_weeks"] == 4
        assert payload["trace_id"].startswith("sim-")

        explain = client.get(f"/api/explain/{payload['trace_id']}")
        assert explain.status_code == 200
        assert explain.json()["evidence"]


def test_medlaw_check_detects_violations() -> None:
    with TestClient(app) as client:
        response = client.post("/api/medlaw/check", json={"text": "100% 효과와 최고 결과"})
        assert response.status_code == 200
        keywords = {item["keyword"] for item in response.json()["violations"]}
        assert {"100% 효과", "최고"}.issubset(keywords)


def test_asset_endpoints() -> None:
    with TestClient(app) as client:
        assert client.get("/api/assets/connectors").status_code == 200
        assert client.get("/api/assets/reviews").status_code == 200
        assert client.get("/api/assets/promotions").status_code == 200
