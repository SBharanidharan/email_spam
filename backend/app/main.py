import os
import sys
import json
import logging
from contextlib import asynccontextmanager
import joblib
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("email-detect-backend")

# Ensure parent directory is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.preprocess import preprocess_text

# Global dictionary to hold model artifacts
model_artifacts = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load model files on startup
    model_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "model"))
    
    vectorizer_path = os.path.join(model_dir, "tfidf_vectorizer.pkl")
    nb_path = os.path.join(model_dir, "naive_bayes_model.pkl")
    lr_path = os.path.join(model_dir, "logistic_regression_model.pkl")
    svm_path = os.path.join(model_dir, "support_vector_machine_model.pkl")
    ens_path = os.path.join(model_dir, "ensemble_model_model.pkl")
    metrics_path = os.path.join(model_dir, "metrics_comparison.json")
    
    logger.info(f"Looking for model files in: {model_dir}")
    
    try:
        if os.path.exists(vectorizer_path):
            model_artifacts["vectorizer"] = joblib.load(vectorizer_path)
            logger.info("Loaded TF-IDF Vectorizer.")
        else:
            logger.warning("TF-IDF Vectorizer not found. Did you run the training script?")

        if os.path.exists(nb_path):
            model_artifacts["Naive Bayes"] = joblib.load(nb_path)
            logger.info("Loaded Naive Bayes model.")

        if os.path.exists(lr_path):
            model_artifacts["Logistic Regression"] = joblib.load(lr_path)
            logger.info("Loaded Logistic Regression model.")

        if os.path.exists(svm_path):
            model_artifacts["Support Vector Machine"] = joblib.load(svm_path)
            logger.info("Loaded Support Vector Machine model.")

        if os.path.exists(ens_path):
            model_artifacts["Ensemble Model"] = joblib.load(ens_path)
            logger.info("Loaded Ensemble model.")
            
        if os.path.exists(metrics_path):
            with open(metrics_path, "r") as f:
                model_artifacts["metrics"] = json.load(f)
            logger.info("Loaded metrics comparison file.")
        else:
            # Fallback mock metrics if training hasn't run yet
            model_artifacts["metrics"] = {}
            logger.warning("Metrics comparison file not found.")
            
    except Exception as e:
        logger.error(f"Error loading model files: {e}")
        
    yield
    model_artifacts.clear()

app = FastAPI(
    title="Email Spam Detection API",
    description="Backend API service for real-time email spam classification using trained ML models.",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Schemas
class PredictRequest(BaseModel):
    text: str = Field(..., description="The raw email text to classify", min_length=1, max_length=10000)
    model_name: str = Field("Ensemble Model", description="Name of the model to use for prediction")

class PredictResponse(BaseModel):
    prediction: str = Field(..., description="'Spam' or 'Not Spam'")
    label: int = Field(..., description="1 for Spam, 0 for Not Spam")
    probability: float = Field(..., description="Probability of being Spam (0.0 to 1.0)")
    confidence: float = Field(..., description="Model's confidence in its classification decision (0.0 to 1.0)")
    model_used: str = Field(..., description="The name of the classifier model used")
    processed_text: str = Field(..., description="The cleaned and preprocessed email text used by the model")

# Helper to check if model artifacts are loaded
def check_artifacts_loaded(model_name: str):
    if "vectorizer" not in model_artifacts:
        raise HTTPException(status_code=503, detail="TF-IDF Vectorizer is not loaded on the backend. Please run model training.")
    if model_name not in model_artifacts:
        raise HTTPException(status_code=503, detail=f"Model '{model_name}' is not loaded on the backend. Please run model training.")

@app.post("/api/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    # Validate model selection
    valid_models = ["Naive Bayes", "Logistic Regression", "Ensemble Model"]
    selected_model = request.model_name
    
    if selected_model not in valid_models:
        raise HTTPException(status_code=400, detail=f"Invalid model name. Choose from: {valid_models}")
        
    # Check if loaded
    check_artifacts_loaded(selected_model)
    
    # Extract text and run preprocess
    raw_text = request.text
    processed_text = preprocess_text(raw_text)
    
    # If the text is empty or has no content after preprocessing
    if not processed_text.strip():
        # Fallback to Ham with zero spam probability
        return PredictResponse(
            prediction="Not Spam",
            label=0,
            probability=0.0,
            confidence=1.0,
            model_used=selected_model,
            processed_text=""
        )
        
    try:
        # Load artifacts
        vectorizer = model_artifacts["vectorizer"]
        model = model_artifacts[selected_model]
        
        # Vectorize
        vectorized_text = vectorizer.transform([processed_text])
        
        # Predict class
        pred = int(model.predict(vectorized_text)[0])
        
        # Predict probability
        # NB, Logistic Regression, and SVM (if trained with probability=True) support predict_proba
        proba_matrix = model.predict_proba(vectorized_text)
        spam_probability = float(proba_matrix[0][1])  # Class 1 is Spam
        
        # Confidence score
        # Confidence is the probability of the predicted class
        confidence = float(proba_matrix[0][pred])
        
        prediction_str = "Spam" if pred == 1 else "Not Spam"
        
        return PredictResponse(
            prediction=prediction_str,
            label=pred,
            probability=spam_probability,
            confidence=confidence,
            model_used=selected_model,
            processed_text=processed_text
        )
        
    except Exception as e:
        logger.error(f"Error during prediction: {e}")
        raise HTTPException(status_code=500, detail=f"Internal prediction error: {str(e)}")

@app.get("/api/metrics")
def get_metrics():
    # If metrics are loaded from file, return them
    if "metrics" in model_artifacts and model_artifacts["metrics"]:
        return model_artifacts["metrics"]
        
    # Fallback to checking the file directly
    model_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "model"))
    metrics_path = os.path.join(model_dir, "metrics_comparison.json")
    
    if os.path.exists(metrics_path):
        try:
            with open(metrics_path, "r") as f:
                metrics = json.load(f)
            model_artifacts["metrics"] = metrics
            return metrics
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to read metrics file: {str(e)}")
            
    # If metrics file doesn't exist yet, return a warning/empty dict
    return {
        "status": "warning",
        "message": "Model training metrics are not available. Please run model training first.",
        "Naive Bayes": {"accuracy": 0, "precision": 0, "recall": 0, "f1_score": 0, "confusion_matrix": [[0,0],[0,0]]},
        "Logistic Regression": {"accuracy": 0, "precision": 0, "recall": 0, "f1_score": 0, "confusion_matrix": [[0,0],[0,0]]},
        "Support Vector Machine": {"accuracy": 0, "precision": 0, "recall": 0, "f1_score": 0, "confusion_matrix": [[0,0],[0,0]]},
        "Ensemble Model": {"accuracy": 0, "precision": 0, "recall": 0, "f1_score": 0, "confusion_matrix": [[0,0],[0,0]]}
    }

@app.get("/api/health")
def health_check():
    loaded_artifacts = list(model_artifacts.keys())
    return {
        "status": "healthy",
        "loaded_models_and_artifacts": loaded_artifacts
    }

# Serve Frontend static assets
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))

# Mount frontend files under /static
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

# Serve index.html at root
@app.get("/")
def serve_home():
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Frontend index.html not found.")

