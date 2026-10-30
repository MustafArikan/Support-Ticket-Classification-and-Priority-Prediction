import importlib
from unittest.mock import Mock
import pytest
from fastapi.testclient import TestClient

api = importlib.import_module("src.api.main")


@pytest.fixture
def client(monkeypatch):
    model = Mock()
    model.predict.return_value = dict(
        category="Technical Issue", priority="high", confidence=0.9
    )
    monkeypatch.setattr(api, "BERT_MODEL", None)
    monkeypatch.setattr(api, "create_model", Mock(return_value=model))
    with TestClient(api.app) as test_client:
        yield test_client, model


def test_health_check(client):
    response = client[0].get("/health")
    assert response.status_code == 200
    assert response.json() == dict(status="healthy", model_loaded=True)


def test_predict_success(client):
    response = client[0].post("/predict", json={"text": "My internet is not working!"})
    assert response.status_code == 200
    assert response.json()["confidence"] == 0.9


@pytest.mark.parametrize("text", ["short", " " * 12, "x" * 5001])
def test_invalid_text(client, text):
    assert client[0].post("/predict", json={"text": text}).status_code == 422
    client[1].predict.assert_not_called()


def test_predict_xss_sanitization(client):
    text = "Issue <script>alert('xss')</script> please fix."
    assert client[0].post("/predict", json={"text": text}).status_code == 200
    cleaned = client[1].predict.call_args.args[0]
    assert "<script>" not in cleaned
    assert "&lt;script&gt;" in cleaned


def test_model_load_failure(monkeypatch):
    monkeypatch.setattr(api, "BERT_MODEL", None)
    monkeypatch.setattr(
        api, "create_model", Mock(side_effect=OSError("missing checkpoint"))
    )
    with TestClient(api.app) as client:
        assert client.get("/health").status_code == 503
        assert (
            client.post(
                "/predict", json={"text": "My internet is not working!"}
            ).status_code
            == 503
        )


def test_prediction_failure(client):
    client[1].predict.side_effect = RuntimeError("private model error")
    response = client[0].post("/predict", json={"text": "My internet is not working!"})
    assert response.status_code == 500
    assert "private model error" not in response.text
