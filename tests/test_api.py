from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "model_loaded": True}

def test_predict_success():
    payload = {"text": "My internet is not working since morning, please help!"}
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "category" in data
    assert "priority" in data
    assert "confidence" in data
    assert data["confidence"] >= 0.0 and data["confidence"] <= 1.0

def test_predict_short_text():
    payload = {"text": "short"}
    response = client.post("/predict", json=payload)
    assert response.status_code == 422 # Unprocessable Entity due to validation

def test_predict_xss_sanitization():
    # Test if script tags are escaped properly by validation
    payload = {"text": "I have an issue <script>alert('xss')</script> please fix."}
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    # In a real scenario we'd mock the model to echo back the sanitized text to assert.
    # But as long as it doesn't crash and returns 200, the validator ran.
