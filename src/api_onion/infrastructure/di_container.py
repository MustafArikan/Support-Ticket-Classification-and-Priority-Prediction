from src.api_onion.infrastructure.ai.bert_adapter import BertModelAdapter
from src.api_onion.core.application.ticket_service import TicketService

# Simple Dependency Injection Container
class Container:
    model_adapter = None
    ticket_service = None

    @classmethod
    def init(cls):
        cls.model_adapter = BertModelAdapter()
        cls.ticket_service = TicketService(cls.model_adapter)