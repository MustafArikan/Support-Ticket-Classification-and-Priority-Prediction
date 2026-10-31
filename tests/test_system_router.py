from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api_onion.presentation.routers import system_router


@pytest.fixture
def client(monkeypatch):
    monkeypatch.delenv("ENABLE_LOCAL_SERVICE_CONTROL", raising=False)
    process = Mock()
    monkeypatch.setattr(system_router.subprocess, "Popen", process)
    app = FastAPI()
    app.include_router(system_router.router, prefix="/api/v1/system")
    with TestClient(app) as test_client:
        yield test_client, process


def test_service_control_is_disabled_by_default(client):
    response = client[0].post("/api/v1/system/start", json={"service": "mlflow"})
    assert response.status_code == 404
    client[1].assert_not_called()


def test_opted_in_control_uses_argument_list(client, monkeypatch):
    monkeypatch.setenv("ENABLE_LOCAL_SERVICE_CONTROL", "true")
    response = client[0].post("/api/v1/system/start", json={"service": "MLflow"})
    assert response.status_code == 200
    assert client[1].call_args.args == (["docker", "compose", "up", "-d", "mlflow"],)
    assert not client[1].call_args.kwargs.get("shell", False)


def test_unknown_service_stays_a_client_error(client, monkeypatch):
    monkeypatch.setenv("ENABLE_LOCAL_SERVICE_CONTROL", "true")
    response = client[0].post("/api/v1/system/start", json={"service": "unknown"})
    assert response.status_code == 400
    client[1].assert_not_called()


def test_process_failure_does_not_disclose_host_details(client, monkeypatch):
    monkeypatch.setenv("ENABLE_LOCAL_SERVICE_CONTROL", "true")
    client[1].side_effect = OSError("private host path")
    response = client[0].post("/api/v1/system/start", json={"service": "grafana"})
    assert response.status_code == 500
    assert "private host path" not in response.text
