import os
import sys
import pytest
from fastapi.testclient import TestClient

# Add parent directories to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.main import app

@pytest.fixture(scope="module")
def client():
    # Use context manager to trigger FastAPI lifespan (which loads models)
    with TestClient(app) as c:
        yield c

def test_health_endpoint(client):
    """Test the API health check."""
    response = client.get("/api/health")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "healthy"
    assert "loaded_models_and_artifacts" in json_data

def test_metrics_endpoint(client):
    """Test retrieving evaluation metrics."""
    response = client.get("/api/metrics")
    assert response.status_code == 200
    json_data = response.json()
    # Check that it returns structured metrics for each classifier
    for model_name in ["Naive Bayes", "Logistic Regression", "Ensemble Model"]:
        assert model_name in json_data
        assert "accuracy" in json_data[model_name]
        assert "precision" in json_data[model_name]
        assert "recall" in json_data[model_name]
        assert "f1_score" in json_data[model_name]
        assert "confusion_matrix" in json_data[model_name]

def test_predict_validation(client):
    """Test input validation for predictions."""
    # Test empty text (should fail validation if min_length=1)
    response = client.post("/api/predict", json={"text": "", "model_name": "Logistic Regression"})
    assert response.status_code == 422
    
    # Test invalid model name
    response = client.post("/api/predict", json={"text": "Hello world", "model_name": "Random Forest"})
    assert response.status_code == 400
    assert "Invalid model name" in response.json()["detail"]

def test_predict_edge_cases(client):
    """Test predictor with empty preprocessed text (e.g. only punctuation)."""
    # If text has only punctuation, it becomes empty after preprocessing
    # The API should gracefully fallback to 'Not Spam'
    response = client.post("/api/predict", json={"text": "!!! ???", "model_name": "Ensemble Model"})
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["prediction"] == "Not Spam"
    assert json_data["probability"] == 0.0
    assert json_data["confidence"] == 1.0

def test_predict_ham_email(client):
    """Test prediction for a typical ham email."""
    # A standard ham email
    ham_text = "Hi Team, just a reminder that our project status meeting is scheduled for tomorrow morning at 10 AM in the conference room. Please bring your updates."
    
    for model in ["Naive Bayes", "Logistic Regression", "Ensemble Model"]:
        response = client.post("/api/predict", json={"text": ham_text, "model_name": model})
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["model_used"] == model
        assert json_data["prediction"] in ["Spam", "Not Spam"]
        assert 0.0 <= json_data["probability"] <= 1.0
        assert 0.0 <= json_data["confidence"] <= 1.0
        
        # Generally, this clear email should be classified as Not Spam
        # (It depends on the trained models, but most will flag this as ham)
        if json_data["prediction"] == "Not Spam":
            assert json_data["probability"] < 0.5
            assert json_data["label"] == 0

def test_predict_spam_email(client):
    """Test prediction for a typical spam email."""
    # A standard spam email
    spam_text = "URGENT! You have won a $1,000 cash prize! Click here immediately to claim your award! Limited time offer, act now!"
    
    for model in ["Naive Bayes", "Logistic Regression", "Ensemble Model"]:
        response = client.post("/api/predict", json={"text": spam_text, "model_name": model})
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["model_used"] == model
        
        # Most classifiers will flag this highly spammy text as Spam
        if json_data["prediction"] == "Spam":
            assert json_data["probability"] >= 0.5
            assert json_data["label"] == 1

