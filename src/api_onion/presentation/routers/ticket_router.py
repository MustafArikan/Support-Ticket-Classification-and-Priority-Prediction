from fastapi import APIRouter, HTTPException, Depends
from src.api_onion.core.domain.entities import Ticket, PredictionResult
from src.api_onion.infrastructure.di_container import Container

router = APIRouter()

def get_ticket_service():
    if not Container.ticket_service or not getattr(Container.model_adapter, 'is_loaded', False):
        raise HTTPException(status_code=503, detail="Service unavailable: Model not loaded")
    return Container.ticket_service

@router.post("/predict", response_model=PredictionResult)
async def predict_ticket(ticket: Ticket, service = Depends(get_ticket_service)):
    try:
        return service.classify_ticket(ticket)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))