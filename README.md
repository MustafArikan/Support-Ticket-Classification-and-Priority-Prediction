# 🎫 Support Ticket Classification & Priority Prediction

**An end-to-end, multilingual MLOps system that reads a raw customer support ticket and instantly returns its category, priority, and an explanation for the decision — served through a monitored, containerized, auto-scaling API.**

[![Python](https://img.shields.io/badge/Python-3.10-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.103-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PyTorch](https://img.shields.io/badge/PyTorch-Transformers-EE4C2C?logo=pytorch&logoColor=white)](https://pytorch.org/)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-HPA-326CE5?logo=kubernetes&logoColor=white)](https://kubernetes.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 1. What This Project Does

Support teams spend real time manually reading, tagging, and prioritizing every incoming ticket before anyone can act on it. This project automates that first triage step with a fine-tuned multilingual transformer:

1. **Classifies** the ticket into a support **category** (Technical Issue, Billing, Refund, Account Management, General Inquiry)
2. **Predicts** its **priority** (Low / Medium / High / Critical)
3. **Explains** the decision with the most influential words (SHAP + LIME)
4. **Serves** all of the above through a FastAPI service that is Dockerized, deployable on Kubernetes with autoscaling, and observable via Prometheus/Grafana/Loki

> *"Support teams manually triage and prioritize incoming tickets. I automated this with a multilingual NLP model, made its decisions explainable, and shipped it as a production-style system with CI/CD, container orchestration, and live monitoring."*

![Architecture diagram](architecture_diagram.png)

---

## 2. Table of Contents

- [What This Project Does](#1-what-this-project-does)
- [Key Features](#3-key-features)
- [Tech Stack](#4-tech-stack)
- [Repository Structure](#5-repository-structure)
- [Dataset](#6-dataset)
- [Model](#7-model)
- [Getting Started](#8-getting-started)
- [Running the Full Stack with Docker Compose](#9-running-the-full-stack-with-docker-compose)
- [Kubernetes Deployment](#10-kubernetes-deployment)
- [API Reference](#11-api-reference)
- [Testing & Load Testing](#12-testing--load-testing)
- [Monitoring & Observability](#13-monitoring--observability)
- [CI/CD](#14-cicd)
- [Project Status & Roadmap](#15-project-status--roadmap)
- [Known Limitations](#16-known-limitations)
- [License](#17-license)

---

## 3. Key Features

- 🌍 **Multilingual out of the box** — trained on English, German, and Turkish tickets with a single shared model
- 🧠 **Multi-task transformer** — one backbone, four prediction heads (`type`, `queue`, `category`, `priority`)
- 🔍 **Explainable predictions** — combined SHAP + LIME word-importance scores returned alongside every prediction
- ⚡ **Two ready-to-use frontends** — a polished React + TypeScript + Tailwind dashboard, and a bilingual (TR/EN) Streamlit demo for quick sharing
- 📦 **Two API implementations** — a simple, single-file FastAPI service and a refactored **Onion/Clean Architecture** version (domain → application → infrastructure → presentation) for the dashboard
- 📊 **Full observability stack** — Prometheus metrics (including custom AI business metrics), Grafana dashboards, Loki + Promtail for logs, node-exporter for host metrics
- 📈 **Statistical drift detection** — Kolmogorov–Smirnov test comparing live traffic against the training distribution
- 🚀 **Cloud-native deployment** — multi-stage Docker build, Kubernetes Deployment/Service/HPA/ConfigMap manifests with liveness & readiness probes
- ✅ **CI pipeline** — automatic linting (flake8/black), testing (pytest), and Docker build verification on every push

---

## 4. Tech Stack

| Layer | Technology |
|---|---|
| **Model** | PyTorch, HuggingFace `transformers`, `bert-base-multilingual-cased` (multi-task head), `safetensors` |
| **Explainability** | SHAP, LIME |
| **Experimentation** | Jupyter notebooks (EDA → baselines → neural baselines → BERT → XLM-R fine-tuning), MLflow |
| **Backend API** | FastAPI, Pydantic v2, Uvicorn, `prometheus-fastapi-instrumentator` |
| **Dashboard (primary)** | React 19, TypeScript, Vite, Tailwind CSS, Axios, PapaParse, lucide-react |
| **Demo UI (secondary)** | Streamlit |
| **Containers** | Docker (multi-stage build, non-root runtime user), Docker Compose |
| **Orchestration** | Kubernetes (Deployment, Service, HorizontalPodAutoscaler, ConfigMap) |
| **Monitoring** | Prometheus, Grafana, Loki, Promtail, node-exporter |
| **CI/CD** | GitHub Actions (black, flake8, pytest, Docker build) |
| **Testing** | pytest, `TestClient`, Locust (load testing) |

---

## 5. Repository Structure

```
Support-Ticket-Classification-and-Priority-Prediction/
├── app.py                          # Streamlit demo UI (bilingual TR/EN, single + batch analysis)
├── architecture_diagram.png
├── docker-compose.yml              # Full stack: api, frontend, prometheus, grafana, loki, promtail, mlflow
├── docker/
│   ├── Dockerfile                  # Multi-stage build for the FastAPI service
│   ├── prometheus.yml
│   └── grafana/                    # Provisioned datasources + dashboards (FastAPI, nginx, node-exporter…)
├── k8s/
│   ├── deployment.yaml             # 2 replicas, resource limits, liveness/readiness probes
│   ├── service.yaml                # LoadBalancer, port 80 → 8000
│   ├── hpa.yaml                    # Autoscale 2–10 pods on CPU 70% / memory 80%
│   └── configmap.yaml
├── data/
│   ├── raw/                        # Source EN/DE/TR ticket data
│   ├── processed/                  # train / val / test splits (~32.7K tickets total)
│   └── data_validation.py
├── notebooks/
│   ├── 01_eda.ipynb
│   ├── 02_baseline_modeling.ipynb
│   ├── 03_neural_baselines.ipynb
│   ├── 04_bert_finetuning.ipynb
│   ├── 05_xlmr_finetuning.ipynb
│   └── data_generation.ipynb
├── src/
│   ├── api/                        # Legacy/simple FastAPI service (used by tests & the Docker image)
│   │   ├── main.py
│   │   ├── schemas.py
│   │   └── bert_inference.py
│   ├── api_onion/                  # Refactored Clean/Onion Architecture API (used by the React dashboard)
│   │   ├── core/domain/            # Entities (Ticket, PredictionResult) + ports (ModelInterface)
│   │   ├── core/application/       # TicketService (use case)
│   │   ├── infrastructure/         # BertModelAdapter, DI container, Prometheus metrics
│   │   └── presentation/           # FastAPI app + routers (/api/v1/tickets, /api/v1/system)
│   └── monitoring/
│       └── drift_detection.py      # KS-test based drift check
├── frontend/                       # React + TypeScript + Tailwind dashboard
│   ├── src/App.tsx
│   └── Dockerfile
├── tests/
│   ├── test_api.py
│   └── locustfile.py
├── .github/workflows/ci.yml
├── requirements.txt
└── LICENSE
```

---

## 6. Dataset

- **~32,750 tickets** total — **22,927** train / **4,912** validation / **4,915** test (stratified split)
- **Languages:** English, German, and Turkish, combined from `en_de_mix_dataset.csv` and `tr_dataset.csv/.jsonl` into `tickets_combined.jsonl`
- **Label schema** (four attributes per ticket — the model predicts all four, though the API currently surfaces two of them, see [Known Limitations](#16-known-limitations)):

  | Field | Classes |
  |---|---|
  | `type` | Change, Incident, Problem, Request |
  | `queue` | Billing and Payments, Customer Service, General Inquiry, Human Resources, IT Support, Product Support, Returns and Exchanges, Sales and Pre-Sales, Service Outages and Maintenance, Technical Support |
  | `category` *(exposed via API)* | Account Management, Billing, General Inquiry, Refund, Technical Issue |
  | `priority` *(exposed via API)* | Critical, High, Low, Medium |

- **Preprocessing / validation:** `data/data_validation.py` enforces the schema before training; `notebooks/01_eda.ipynb` covers class balance, text length, and language distribution.

---

## 7. Model

The production model (`src/api/bert_inference.py`, `src/api_onion/infrastructure/ai/bert_adapter.py`) is a **multi-task transformer**:

- **Backbone:** `bert-base-multilingual-cased`, shared across all four tasks
- **Heads:** one linear classification head per label field (`type`, `queue`, `category`, `priority`), each trained jointly on top of the pooled `[CLS]` representation
- **Confidence score:** the average softmax confidence of the `category` and `priority` predictions
- **Explainability:** for every prediction, the service runs both a SHAP `Text` explainer and a LIME `LimeTextExplainer` against the `category` head and merges their top-scoring words into a single `explainability` map, de-duplicating overlapping terms
- **Checkpoint:** loaded from `models/bert_multitask_checkpoints/checkpoint-<step>/model.safetensors` at API startup (this directory is intentionally **not** committed to the repo — see [Getting Started](#8-getting-started) for how to obtain or train one)

Earlier stages of the pipeline — TF-IDF/Logistic Regression baselines, a neural baseline, and an `xlm-roberta-base` fine-tune — are preserved in `notebooks/02–05` as a comparison trail showing why the multi-task mBERT model was ultimately chosen for deployment.

---

## 8. Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+ (for the React dashboard)
- Docker & Docker Compose (for the full-stack setup)
- A trained model checkpoint under `models/bert_multitask_checkpoints/checkpoint-<step>/model.safetensors` (train one via `notebooks/04_bert_finetuning.ipynb`, or place a pretrained checkpoint there yourself)

### 1. Clone and install Python dependencies

```bash
git clone https://github.com/MustafArikan/Support-Ticket-Classification-and-Priority-Prediction.git
cd Support-Ticket-Classification-and-Priority-Prediction

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Run the API

**Option A — the simple/legacy service** (what the Docker image and the test suite use, port `8000`):

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Option B — the Onion Architecture service** (what the React dashboard talks to, port `8001`):

```bash
uvicorn src.api_onion.presentation.main:app --host 0.0.0.0 --port 8001 --reload
```

Either way, check it's alive:

```bash
curl http://localhost:8000/health
```

### 3. Run a frontend

**React dashboard** (recommended — batch upload, history, dark mode, service panel):

```bash
cd frontend
npm install
npm run dev
```

By default it points to `http://localhost:8001` (override with a `VITE_API_URL` env var).

**Streamlit demo** (single-file, bilingual, quick to share):

```bash
streamlit run app.py
```

Defaults to `http://localhost:8000` for the API.

---

## 9. Running the Full Stack with Docker Compose

`docker-compose.yml` brings up the API, the React frontend, and the entire monitoring stack together:

```bash
docker compose up --build
```

| Service | URL | Purpose |
|---|---|---|
| `api` | http://localhost:8000 | FastAPI inference service |
| `frontend` | http://localhost:8085 | React dashboard |
| `mlflow` | http://localhost:5000 | Experiment tracking / model registry |
| `prometheus` | http://localhost:9090 | Metrics collection |
| `grafana` | http://localhost:3000 | Dashboards (FastAPI, AI business metrics, nginx, node-exporter) |
| `loki` / `promtail` | — | Log aggregation |
| `node-exporter` | — | Host-level metrics |

---

## 10. Kubernetes Deployment

Manifests live under `k8s/` and assume a local cluster (Minikube/Kind) with the Docker image already built:

```bash
docker build -t support-ticket-api:latest -f docker/Dockerfile .

minikube start
kubectl apply -f k8s/

kubectl get pods
kubectl get hpa
```

- **Deployment:** 2 replicas, `256Mi`/`250m` requests, `512Mi`/`500m` limits, liveness & readiness probes on `/health`
- **HPA:** scales 2 → 10 pods on 70% CPU or 80% memory utilization
- **Service:** `LoadBalancer` exposing port `80` → container port `8000`

To see the HPA trigger, run a load test against the exposed service (see below) while watching `kubectl get hpa -w`.

---

## 11. API Reference

### Legacy service (`src/api/main.py`) — served on `:8000`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Returns `{"status": "healthy", "model_loaded": true}` |
| `POST` | `/predict` | Body: `{"text": "..."}` (10–5000 chars) → `{"category", "priority", "confidence", "explanation"}` |

### Onion Architecture service (`src/api_onion`) — served on `:8001`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Model-load status via the DI container |
| `GET` | `/metrics` | Prometheus metrics (via `prometheus-fastapi-instrumentator`) |
| `POST` | `/api/v1/tickets/predict` | Body: `{"text": "..."}` → `{"category", "priority", "confidence", "explainability"}` |
| `POST` | `/api/v1/system/start` | Local dev convenience — starts `mlflow`/`prometheus`/`grafana` via Docker Compose, or opens the Minikube dashboard |

Every request is validated and sanitized (HTML-escaped, script/`javascript:` patterns stripped, whitespace-only input rejected) before reaching the model.

---

## 12. Testing & Load Testing

```bash
# Unit / integration tests
pytest tests/

# Load test against a running API (adjust host as needed)
locust -f tests/locustfile.py --host http://localhost:8000
```

`tests/test_api.py` covers the health check, a successful prediction, input-length validation (422 on short text), and XSS-sanitization handling. `tests/locustfile.py` simulates weighted traffic (3:1 prediction-to-health-check ratio) for stress-testing the autoscaler.

---

## 13. Monitoring & Observability

- **Custom AI metrics** (`src/api_onion/infrastructure/monitoring/metrics.py`): a `Counter` of tickets processed per category/priority, and a `Histogram` of model confidence scores
- **Standard FastAPI metrics** via `prometheus-fastapi-instrumentator`, exposed at `/metrics`
- **Grafana dashboards** pre-provisioned under `docker/grafana/dashboards/`: FastAPI performance, AI business metrics, nginx, Loki logs, and node-exporter host metrics
- **Drift detection** (`src/monitoring/drift_detection.py`): a two-sample Kolmogorov–Smirnov test flags a warning when the distribution of a live metric (e.g. text length or confidence) diverges from the training-time reference at `p < 0.05`

---

## 14. CI/CD

`.github/workflows/ci.yml` runs on every push and pull request to `main`:

1. Install dependencies
2. `black --check` for formatting
3. `flake8` (syntax errors + complexity/line-length checks)
4. `pytest` for the test suite
5. On push to `main`: build the Docker image to verify it compiles cleanly

> Pushing the built image to a registry (Docker Hub / GHCR) is stubbed out in the workflow and is one of the next steps — see [Roadmap](#15-project-status--roadmap).

---

## 16. Known Limitations

- **Two live APIs, one model:** the containerized/tested API (`src/api/main.py`) and the React dashboard's API (`src/api_onion`) are separate FastAPI apps that both load the same checkpoint independently. They haven't been merged yet — pick the one that matches what you're integrating with (see [API Reference](#11-api-reference)).
- **`type` and `queue` are computed but not returned:** the model has four output heads, but both API responses currently only surface `category` and `priority`.
- **`/api/v1/system/start` is a local development convenience**, not an authenticated production endpoint — it shells out to `docker compose` / `minikube` based on a whitelisted service name. Don't expose it publicly as-is.
- **Model checkpoints are not committed** (by design — see `.gitignore`); you need to train one or supply your own before the API can serve predictions.
- **CI does not yet push to a registry or deploy to Kubernetes** — those steps are manual today (see Roadmap above).

---

## 17. License

Released under the [MIT License](LICENSE) © 2026 Mustafa Arıkan.
