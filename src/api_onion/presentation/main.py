from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from src.api_onion.presentation.routers.ticket_router import router as ticket_router
from src.api_onion.presentation.routers.system_router import router as system_router
from src.api_onion.infrastructure.di_container import Container
from prometheus_fastapi_instrumentator import Instrumentator

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Onion Architecture Ticket API",
    description="Refactored using Domain, Application, Infrastructure, Presentation layers."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

instrumentator = Instrumentator().instrument(app)

@app.on_event("startup")
async def startup_event():
    Container.init()
    instrumentator.expose(app, endpoint="/metrics")

app.include_router(ticket_router, prefix="/api/v1/tickets", tags=["Tickets"])
app.include_router(system_router, prefix="/api/v1/system", tags=["System"])

@app.get("/health")
async def health_check():
    loaded = getattr(Container.model_adapter, 'is_loaded', False) if Container.model_adapter else False
    return {"status": "healthy", "model_loaded": loaded}