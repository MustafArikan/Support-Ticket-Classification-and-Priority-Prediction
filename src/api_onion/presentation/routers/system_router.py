from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import subprocess
import os

router = APIRouter()

class ServiceRequest(BaseModel):
    service: str

@router.post('/start')
async def start_service(req: ServiceRequest):
    service = req.service.lower()
    try:
        if service in ['mlflow', 'prometheus', 'grafana']:
            subprocess.Popen('docker-compose up -d ' + service, shell=True, cwd=os.getcwd())
            return {'status': f'Starting {service} via docker-compose...'}
        elif service == 'kubernetes':
            subprocess.Popen('minikube dashboard', shell=True, cwd=os.getcwd())
            return {'status': 'Starting kubernetes dashboard...'}
        else:
            raise HTTPException(status_code=400, detail='Unknown service')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

