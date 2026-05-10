from fastapi.testclient import TestClient

from app.main import app


def test_audit_requires_owner_and_supports_filters() -> None:
    with TestClient(app) as client:
        forbidden = client.get("/api/audit", headers={"X-User-Role": "staff"})
        assert forbidden.status_code == 403

        allowed = client.get("/api/audit?domain=brand", headers={"X-User-Role": "owner"})
        assert allowed.status_code == 200


def test_signals_refresh_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get("/api/signals?refresh=true")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


def test_analytics_endpoints_are_cached_shape() -> None:
    with TestClient(app) as client:
        campaign = client.get("/api/analytics/campaign")
        channels = client.get("/api/analytics/channels")
        assert campaign.status_code == 200
        assert channels.status_code == 200
        assert isinstance(campaign.json(), list)
        assert isinstance(channels.json(), list)
