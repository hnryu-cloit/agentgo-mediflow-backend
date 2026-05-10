from fastapi.testclient import TestClient

from app.main import app


def test_save_and_get_clinic_profile() -> None:
    payload = {
        "hospital_name": "테스트 피부과",
        "clinic_type": "PREMIUM",
        "target_audience": "30-40대 직장 여성",
        "doctor_philosophy": "과장 없는 설명과 회복 기간 안내",
        "signature_procedures": ["피코토닝", "잡티케어"],
        "brand_tone": ["신뢰감", "친근함"],
        "banned_terms": ["완치", "100% 효과"],
    }

    with TestClient(app) as client:
        response = client.post("/api/brand", json=payload, headers={"X-User-Role": "marketing_manager"})
        assert response.status_code == 201
        assert response.json()["name"] == "테스트 피부과"

        response = client.get("/api/brand")
        assert response.status_code == 200
        assert response.json()["signature_procedures"] == ["피코토닝", "잡티케어"]


def test_brand_ai_write_returns_trace_id() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/brand/ai-write",
            json={"field": "target_audience"},
            headers={"X-User-Role": "staff"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["field"] == "target_audience"
        assert body["draft"]
        assert body["trace_id"].startswith("brand-")

        explain = client.get(f"/api/explain/{body['trace_id']}")
        assert explain.status_code == 200
        assert explain.json()["actions"]
