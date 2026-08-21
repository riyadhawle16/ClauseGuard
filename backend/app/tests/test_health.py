def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_app_starts(client):
    """Verify the app starts and responds."""
    response = client.get("/health")
    assert response.status_code == 200
