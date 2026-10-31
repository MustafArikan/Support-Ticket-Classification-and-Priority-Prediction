# Support Ticket Classification & Priority Prediction

Classify multilingual support tickets with a multi-task transformer and explore the results through API and dashboard implementations.

This individual ML engineering project combines research notebooks, FastAPI services, React/Streamlit interfaces, and deployment/monitoring examples. A compatible trained checkpoint is required for inference; this repository does not establish a currently deployed or production-ready service.

## Key Features

- English, German, and Turkish ticket preparation and modeling experiments.
- A shared multilingual BERT backbone with `type`, `queue`, `category`, and `priority` heads.
- Two FastAPI implementations exposing category, priority, and confidence.
- SHAP/LIME word-importance explanations in the layered API; the legacy API's explanation field is currently empty.
- React batch analysis/history and a separate Streamlit demo.
- Prometheus instrumentation in the layered API, Grafana dashboards, and drift-analysis code.
- Docker Compose and Kubernetes examples, with CI lint, API tests, frontend checks, and container-build verification.

## Tech Stack

| Layer | Technology |
|---|---|
| Modeling | Python, PyTorch, Hugging Face Transformers, safetensors, scikit-learn |
| Explainability | SHAP, LIME |
| APIs | FastAPI, Pydantic, Uvicorn |
| Interfaces | React 19, TypeScript, Vite 8, Tailwind CSS, Streamlit |
| Experiments | Jupyter, MLflow, pandas, SciPy |
| Operations | Docker Compose, Kubernetes manifests, Prometheus, Grafana, Loki/Promtail |
| Quality | pytest, Black, flake8, Oxlint, TypeScript |

Python requirements include tested application pins alongside unpinned ML libraries; they are not a complete reproducibility lock. NumPy is pinned to the compatible 1.x ABI used by the pinned pandas/SciPy versions. The frontend uses an npm lockfile.

## Architecture & Project Structure

```text
.
├── data/                 # Raw/processed tickets and schema validation script
├── notebooks/            # EDA, baselines, neural models, BERT/XLM-R experiments
├── src/
│   ├── api/              # Legacy API used by the default container
│   ├── api_onion/
│   │   ├── core/         # Domain entities, model port, classification use case
│   │   ├── infrastructure/  # BERT adapter, DI, metrics
│   │   └── presentation/    # Layered API and routers
│   └── monitoring/       # Distribution-drift utility
├── frontend/             # React dashboard
├── app.py                # Streamlit demo
├── tests/                # API, decoding, service-control, and load-test code
├── docker/               # API image and monitoring configuration
├── k8s/                  # Example deployment, service, HPA, and configuration
└── docker-compose.yml
```

The APIs load their models independently. Their paths and response fields differ:

| Service | Prediction route | Explanation behavior |
|---|---|---|
| Legacy | `POST /predict` | Optional `explanation` is not populated |
| Layered | `POST /api/v1/tickets/predict` | `explainability` contains attempted SHAP/LIME output |

The model uses `bert-base-multilingual-cased`. Both implementations currently expect `models/bert_multitask_checkpoints/checkpoint-20048/model.safetensors` relative to the repository. Label order and architecture must match the checkpoint; an arbitrary safetensors file or XLM-R checkpoint is not compatible. The `type` and `queue` predictions are computed but not exposed by these API response models.

## Getting Started

Use Python 3.10 (the container/CI target) and Node.js 22 for the dashboard. Python 3.11 can be used for isolated lightweight tests but is not the container target.

```bash
git clone https://github.com/MustafArikan/Support-Ticket-Classification-and-Priority-Prediction.git
cd Support-Ticket-Classification-and-Priority-Prediction
python -m venv .venv
```

Activate with `source .venv/bin/activate` on Linux/macOS or `.venv\Scripts\Activate.ps1` in PowerShell.

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Supply a compatible checkpoint at the path above. [The BERT notebook](notebooks/04_bert_finetuning.ipynb) contains the training experiment; review its data paths, label mapping, and export format before attempting to reproduce an artifact. Initial tokenizer/backbone downloads also require network access or a populated Hugging Face cache.

For the React interface, run the layered service bound to localhost:

```bash
uvicorn src.api_onion.presentation.main:app --host 127.0.0.1 --port 8001 --reload
```

In another terminal:

```bash
cd frontend
npm ci
npm run dev
```

For the legacy API and Streamlit demo instead:

```bash
uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload
# Run separately:
streamlit run app.py
```

## Configuration

| Setting | Behavior |
|---|---|
| `VITE_API_URL` | Frontend build/dev variable; defaults to `http://localhost:8001` |
| `HF_HOME` | Hugging Face cache location; Compose uses `/app/.cache` |
| `ENABLE_LOCAL_SERVICE_CONTROL` | Defaults to disabled; `true` enables the layered API's local service-start convenience |
| `MLFLOW_TRACKING_URI` | Compose supplies the tracking-server URL; experiment code must use it explicitly |

`ENABLE_LOCAL_SERVICE_CONTROL=true` is only for a trusted local development instance. It allows callers to request a whitelisted Docker Compose service or the Minikube dashboard. Do not enable it on a public API. It is disabled in the default deployment configuration.

The checkpoint path is currently hardcoded; the example Kubernetes ConfigMap's `MODEL_VERSION` and `ENVIRONMENT` keys do not select a model in the application. Do not put credentials or real customer ticket text in committed example configuration.

## Usage

Legacy API:

```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text":"My internet connection is not working."}'
```

Layered API:

```bash
curl http://localhost:8001/health
curl -X POST http://localhost:8001/api/v1/tickets/predict \
  -H "Content-Type: application/json" \
  -d '{"text":"My internet connection is not working."}'
```

The legacy service returns 503 for health/prediction when the model is unavailable. The layered health route currently returns 200 with `model_loaded: false` when loading failed; inspect that field rather than treating its status code as readiness. Both prediction services reject unavailable models. Layered metrics are exposed at `/metrics`.

## Testing

```bash
python -m pytest tests/
```

Tests cover legacy API validation/errors, checkpoint-free decoding, the local service-control gate/process invocation, and Streamlit initialization with an offline API. They use fake model boundaries and do not measure checkpoint accuracy or SHAP/LIME quality. The decoding test requires PyTorch even without a checkpoint.

Load testing requires a separately running, checkpoint-backed service:

```bash
locust -f tests/locustfile.py --host http://localhost:8000
```

## Development & Quality

```bash
python -m pip install black==26.5.1 flake8==7.3.0
black --check src/ tests/
flake8 src/ tests/ --count --max-complexity=10 --max-line-length=127 --statistics
python -m pip check
cd frontend
npm run lint
npm run build
```

GitHub Actions runs on pushes and pull requests to `main` with read-only repository permissions. Python checks, frontend checks, and the container build are separate jobs. The container builder resolves and builds the complete wheel dependency set; the runtime installs it offline and runs `pip check`. A proposed build change is not verified until the corresponding CI run completes successfully. CI does not publish an image or deploy a cluster.

## Deployment

```bash
docker compose up --build
```

The default Compose API serves the **legacy** API on port 8000 and mounts `./models` read-only. The React image is served on port 8085, but its default URL targets the **layered** API on port 8001, which Compose does not start. Consequently this is not a fully wired dashboard deployment. Run the layered service separately for a local demonstration or align the API entrypoint, frontend build-time URL, monitoring target, and network routing before deploying.

Other Compose ports include MLflow 5000, Prometheus 9090, Grafana 3000, and Loki 3100. Monitoring images use moving tags and several services assume Linux host mounts. Bind/restrict operational ports and configure credentials before any nonlocal use.

Kubernetes files under `k8s/` are examples, not a turnkey inference deployment. They define two replicas and an HPA but do not mount the required checkpoint/cache. The legacy image does not expose the `/metrics` endpoint referenced by monitoring annotations, and resource limits need measurement with a real model. Resolve these gaps and configure registry/image availability before applying them to a cluster.

## Roadmap

- Consolidate the APIs or provide separately tested deployment profiles.
- Make checkpoint selection configurable and validate full checkpoint compatibility.
- Add real-model readiness, explanation, latency, and held-out quality checks.
- Align Compose/Kubernetes, model storage, metrics, frontend routing, and resource sizing.
- Add dependency constraints/locks, authentication, restricted CORS, and operational hardening.

## Contributing

Include a reproduction and regression test for behavior changes. Keep checkpoint-free tests independent of model downloads, report frontend/Python checks separately, and identify any real-model checks you could not run. Do not commit checkpoints, credentials, or sensitive ticket data.

## License

Code is distributed under the [MIT License](LICENSE). Verify source-dataset and pretrained-model terms separately.

## Author

[Mustafa Arıkan](https://github.com/MustafArikan)
