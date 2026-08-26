import re
import html
from pydantic import BaseModel, Field, field_validator
from typing import Optional

class TicketRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=5000, description="The customer support ticket text.")
    
    @field_validator('text')
    @classmethod
    def sanitize_text(cls, v: str) -> str:
        # XSS Protection: Escape HTML characters and remove script tags if any
        v = html.escape(v)
        # Additional cleanup for common injection patterns
        v = re.sub(r'(javascript:|vbscript:|data:)', '', v, flags=re.IGNORECASE)
        # Ensure it's not just whitespace
        if not v.strip():
            raise ValueError("Ticket text cannot be empty or just whitespace.")
        return v.strip()

class TicketResponse(BaseModel):
    category: str = Field(..., description="Predicted category (e.g., Technical Issue, Billing).")
    priority: str = Field(..., description="Predicted priority (Low, Medium, High, Critical).")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model prediction confidence score.")
    # Explainability field (Day 14 placeholder)
    explanation: Optional[dict] = Field(default=None, description="SHAP/LIME explanation data.")
