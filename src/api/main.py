from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import time
import logging
import os

from .schemas import TicketRequest, TicketResponse
from .bert_inference import BertTicketModel

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

# BERT Model placeholder
BERT_MODEL = None

@app.on_event("startup")
async def load_model():
    global BERT_MODEL
    logger.info("Starting up and loading BERT model...")
    
    try:
        model_path = os.path.join(os.path.dirname(__file__), "../../models/bert_multitask_checkpoints/checkpoint-20048")
        BERT_MODEL = BertTicketModel(model_path)
        logger.info("BERT model loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load BERT model: {e}")
        BERT_MODEL = None

@app.post("/predict", response_model=TicketResponse)
async def predict_ticket(request: TicketRequest):
    if not BERT_MODEL:
        raise HTTPException(status_code=503, detail="Model is currently unavailable.")
    
    start_time = time.time()
    try:
        text = request.text
        text_clean = text if text else ""
        
        result = BERT_MODEL.predict(text_clean)
        
        logger.info(f"Prediction successful in {time.time() - start_time:.4f}s")
        
        return TicketResponse(
            category=result['category'],
            priority=result['priority'],
            confidence=result['confidence']
        )
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during prediction.")

@app.get("/health")
async def health_check():
    if not BERT_MODEL:
        raise HTTPException(status_code=503, detail="Service unavailable: Model not loaded")
    return {"status": "healthy", "model_loaded": True}
