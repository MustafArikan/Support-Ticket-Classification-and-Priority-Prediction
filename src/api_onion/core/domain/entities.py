from pydantic import BaseModel, Field
from typing import Optional, Dict

class Ticket(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)

class PredictionResult(BaseModel):
    category: str
    priority: str
    confidence: float
    explainability: Optional[Dict[str, float]] = None