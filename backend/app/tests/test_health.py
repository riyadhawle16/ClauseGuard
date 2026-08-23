def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    # Health endpoint also returns cors_origins for production verification
    assert "cors_origins" in data
    assert isinstance(data["cors_origins"], list)
    assert len(data["cors_origins"]) > 0


def test_app_starts(client):
    """Verify the app starts and responds."""
    response = client.get("/health")
    assert response.status_code == 200
