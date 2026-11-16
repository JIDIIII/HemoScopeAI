def test_health_reports_service_and_missing_model(client):
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["service_status"] == "ok"
    assert payload["model_available"] is False
    assert payload["model_version"] is None
    assert payload["inference_mode"] == "unavailable"
