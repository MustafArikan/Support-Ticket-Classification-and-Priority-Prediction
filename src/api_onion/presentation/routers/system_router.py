from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import subprocess
import os

router = APIRouter()


class ServiceRequest(BaseModel):
    service: str


@router.post("/start")
async def start_service(req: ServiceRequest):
    if os.getenv("ENABLE_LOCAL_SERVICE_CONTROL", "false").lower() != "true":
        raise HTTPException(status_code=404, detail="Not found")

    service = req.service.lower()
    if service in ["mlflow", "prometheus", "grafana"]:
        command = ["docker", "compose", "up", "-d", service]
    elif service == "kubernetes":
        command = ["minikube", "dashboard"]
    else:
        raise HTTPException(status_code=400, detail="Unknown service")

    try:
        subprocess.Popen(command, cwd=os.getcwd())
    except OSError as exc:
        raise HTTPException(
            status_code=500, detail="Unable to start the local service"
        ) from exc
    return {"status": f"Starting {service}..."}
