from src.api_onion.core.domain.entities import Ticket, PredictionResult
from src.api_onion.core.domain.ports import ModelInterface

class TicketService:
    def __init__(self, model_port: ModelInterface):
        self.model = model_port

    def classify_ticket(self, ticket: Ticket) -> PredictionResult:
        # Preprocess if needed
        text_clean = ticket.text.strip()
        
        # Predict via the port
        result_dict = self.model.predict(text_clean)
        
        # Return Domain Entity
        return PredictionResult(
            category=result_dict['category'],
            priority=result_dict['priority'],
            confidence=result_dict['confidence'],
            explainability=result_dict.get('explainability')
        )