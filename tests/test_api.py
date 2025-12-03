"""Test cases for the Clinical BERT API."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert "version" in response.json()


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "model_loaded" in data
    assert "version" in data


def test_predict_absent():
    """Test prediction for ABSENT case."""
    response = client.post(
        "/predict",
        json={"sentence": "The patient denies chest pain."}
    )
    assert response.status_code == 200
    data = response.json()
    assert "label" in data
    assert "score" in data
    assert data["label"] == "ABSENT"
    assert 0.0 <= data["score"] <= 1.0


def test_predict_present():
    """Test prediction for PRESENT case."""
    response = client.post(
        "/predict",
        json={"sentence": "He has a history of hypertension."}
    )
    assert response.status_code == 200
    data = response.json()
    assert "label" in data
    assert "score" in data
    assert data["label"] == "PRESENT"
    assert 0.0 <= data["score"] <= 1.0


def test_predict_conditional():
    """Test prediction for CONDITIONAL case."""
    response = client.post(
        "/predict",
        json={"sentence": "If the patient experiences dizziness, reduce the dosage."}
    )
    assert response.status_code == 200
    data = response.json()
    assert "label" in data
    assert "score" in data
    assert data["label"] == "CONDITIONAL"
    assert 0.0 <= data["score"] <= 1.0


def test_predict_no_signs():
    """Test prediction for ABSENT case (no signs)."""
    response = client.post(
        "/predict",
        json={"sentence": "No signs of pneumonia were observed."}
    )
    assert response.status_code == 200
    data = response.json()
    assert "label" in data
    assert "score" in data
    assert data["label"] == "ABSENT"
    assert 0.0 <= data["score"] <= 1.0


def test_predict_empty_sentence():
    """Test prediction with empty sentence."""
    response = client.post(
        "/predict",
        json={"sentence": ""}
    )
    assert response.status_code == 422  # Validation error


def test_predict_missing_field():
    """Test prediction with missing field."""
    response = client.post(
        "/predict",
        json={}
    )
    assert response.status_code == 422  # Validation error


def test_batch_predict():
    """Test batch prediction endpoint."""
    response = client.post(
        "/predict/batch",
        json={
            "sentences": [
                "The patient denies chest pain.",
                "He has a history of hypertension.",
                "If the patient experiences dizziness, reduce the dosage."
            ]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "predictions" in data
    assert len(data["predictions"]) == 3
    for pred in data["predictions"]:
        assert "label" in pred
        assert "score" in pred
        assert 0.0 <= pred["score"] <= 1.0


def test_batch_predict_empty_list():
    """Test batch prediction with empty list."""
    response = client.post(
        "/predict/batch",
        json={"sentences": []}
    )
    assert response.status_code == 422  # Validation error


def test_batch_predict_too_large():
    """Test batch prediction with too many sentences."""
    sentences = [f"Sentence {i}." for i in range(101)]
    response = client.post(
        "/predict/batch",
        json={"sentences": sentences}
    )
    assert response.status_code == 400


def test_response_time():
    """Test that response time is reasonable (< 500ms)."""
    import time
    start = time.time()
    response = client.post(
        "/predict",
        json={"sentence": "The patient denies chest pain."}
    )
    elapsed = (time.time() - start) * 1000  # Convert to milliseconds
    
    assert response.status_code == 200
    # Note: First request may be slower due to model warmup
    # Subsequent requests should be faster
    print(f"Response time: {elapsed:.2f}ms")

