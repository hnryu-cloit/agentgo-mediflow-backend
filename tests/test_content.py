from fastapi.testclient import TestClient

from app.main import app


def test_generate_nine_channel_subset_with_fallback() -> None:
    request = {
        "event_name": "봄 피부 이벤트",
        "event_start": "2026-05-01",
        "event_end": "2026-05-31",
        "core_message": "상담 후 개인별 피부 관리 계획을 제안합니다",
        "highlights": ["정품 정량", "회복 기간 안내"],
        "channels": ["ig_feed", "ig_story", "seo_blog", "blog", "web", "place", "kakao", "email", "app"],
        "funnel_stage": "conversion",
        "promo_period_weeks": 4,
    }

    with TestClient(app) as client:
        response = client.post("/api/content/generate", json=request, headers={"X-User-Role": "staff"})
        assert response.status_code == 200
        body = response.json()
        assert body["event_name"] == "봄 피부 이벤트"
        assert set(body["channels"].keys()) == set(request["channels"])
        assert body["consistency_checks"]
        assert body["trace_id"].startswith("content-")


def test_generate_empty_channels_rejected() -> None:
    request = {
        "event_name": "봄 피부 이벤트",
        "event_start": "2026-05-01",
        "event_end": "2026-05-31",
        "core_message": "상담 후 개인별 피부 관리 계획을 제안합니다",
        "channels": [],
    }

    with TestClient(app) as client:
        response = client.post("/api/content/generate", json=request, headers={"X-User-Role": "staff"})
        assert response.status_code == 422


def test_generate_requires_staff_role() -> None:
    request = {
        "event_name": "봄 피부 이벤트",
        "event_start": "2026-05-01",
        "event_end": "2026-05-31",
        "core_message": "상담 후 개인별 피부 관리 계획을 제안합니다",
        "channels": ["blog"],
    }

    with TestClient(app) as client:
        response = client.post("/api/content/generate", json=request)
        assert response.status_code == 403


def test_shorts_storyboard_generation() -> None:
    payload = {
        "template_id": "before_after",
        "source_channel": "blog",
        "longform_draft": {
            "headline": "입술 필러 이벤트",
            "body": "개인별 입술 라인과 회복 기간을 상담 후 안내합니다.",
            "cta": "상담 예약하기",
        },
    }

    with TestClient(app) as client:
        response = client.post("/api/content/shorts", json=payload)
        assert response.status_code == 200
        assert len(response.json()["scenes"]) == 3
