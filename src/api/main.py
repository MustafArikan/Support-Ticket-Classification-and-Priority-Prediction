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

# MLflow model placeholder (Will be loaded at startup)
MODEL = None

@app.on_event("startup")
async def load_model():
    global MODEL
    # In a real scenario, this loads from MLflow:
    # import mlflow
    # MODEL = mlflow.pyfunc.load_model("models:/ticket_classifier/staging")
    logger.info("Starting up and loading model... (Mocked for now)")
    MODEL = "loaded" # Placeholder

@app.post("/predict", response_model=TicketResponse)
async def predict_ticket(request: TicketRequest):
    if not MODEL:
        raise HTTPException(status_code=503, detail="Model is currently unavailable.")
    
    start_time = time.time()
    try:
        # Mocking model inference for now since you are fine-tuning
        # text = request.text
        # prediction = MODEL.predict([text])
        
        # Placeholder mock response
        mock_category = "Technical Issue"
        mock_priority = "High"
        mock_confidence = 0.92
        
        logger.info(f"Prediction successful in {time.time() - start_time:.4f}s")
        
        return TicketResponse(
            category=mock_category,
            priority=mock_priority,
            confidence=mock_confidence
        )
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during prediction.")

@app.get("/health")
async def health_check():
    if not MODEL:
        raise HTTPException(status_code=503, detail="Service unavailable: Model not loaded")
    return {"status": "healthy", "model_loaded": True}

# Initialize Prometheus instrumentation
Instrumentator().instrument(app).expose(app, endpoint="/metrics")
