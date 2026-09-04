import pytest
from starlette.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_samples_endpoint():
    response = client.get("/api/samples")
    assert response.status_code == 200
    data = response.json()
    assert "samples" in data
    assert len(data["samples"]) >= 6

def test_batch_manifest_test_endpoint():
    response = client.post("/api/batch/run-manifest-test")
    assert response.status_code == 200
    data = response.json()
    assert data["total_processed"] >= 6
    assert data["avg_time_per_label_ms"] < 1000  # Sub-second benchmark!
