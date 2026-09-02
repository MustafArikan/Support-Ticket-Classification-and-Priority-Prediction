from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
import time
import logging

from .schemas import TicketRequest, TicketResponse

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Support Ticket Classification API",
    description="API for predicting the category and priority of customer support tickets.",
    version="1.0.0"
)

# CORS Middleware (Restrict this in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

import pickle
import os
import time

# Basic ML models placeholder
VECTORIZER = None
MODELS = None

@app.on_event("startup")
async def load_model():
    global VECTORIZER, MODELS
    logger.info("Starting up and loading basic ML models...")
    
    try:
        models_dir = os.path.join(os.path.dirname(__file__), "../../models/basic_baselines")
        
        # Load vectorizer
        with open(os.path.join(models_dir, "vectorizer.pkl"), "rb") as f:
            VECTORIZER = pickle.load(f)
            
        # Load models dict (contains 'category' and 'priority' models)
        with open(os.path.join(models_dir, "models.pkl"), "rb") as f:
            MODELS = pickle.load(f)
            
        logger.info("Basic ML models and vectorizer loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load models: {e}")
        VECTORIZER = None
        MODELS = None

@app.post("/predict", response_model=TicketResponse)
async def predict_ticket(request: TicketRequest):
    if not VECTORIZER or not MODELS:
        raise HTTPException(status_code=503, detail="Model is currently unavailable.")
    
    start_time = time.time()
    try:
        text = request.text
        
        # Preprocess and vectorize
        # Simple filling for NA as in training
        text_clean = text if text else ""
        X_input = VECTORIZER.transform([text_clean])
        
        # Predict Category
        cat_model = MODELS["category"]
        cat_pred = cat_model.predict(X_input)[0]
        cat_probs = cat_model.predict_proba(X_input)[0]
        cat_conf = max(cat_probs)
        
        # Predict Priority
        pri_model = MODELS["priority"]
        pri_pred = pri_model.predict(X_input)[0]
        pri_probs = pri_model.predict_proba(X_input)[0]
        pri_conf = max(pri_probs)
        
        # Calculate combined confidence
        confidence = (cat_conf + pri_conf) / 2.0
        
        logger.info(f"Prediction successful in {time.time() - start_time:.4f}s")
        
        return TicketResponse(
            category=cat_pred,
            priority=pri_pred,
            confidence=float(confidence)
        )
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during prediction.")

@app.get("/health")
async def health_check():
    if not VECTORIZER or not MODELS:
        raise HTTPException(status_code=503, detail="Service unavailable: Model not loaded")
    return {"status": "healthy", "model_loaded": True}

# Initialize Prometheus instrumentation
Instrumentator().instrument(app).expose(app, endpoint="/metrics")
