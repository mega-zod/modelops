# ModelOps AI

AI Model Deployment Agent backend for planning, authorizing, executing, and verifying model deployments.

The first version is intentionally focused on agent-native behavior rather than a generic chatbot:

- accept structured user deployment requests
- analyze hardware constraints
- select a viable serving profile
- produce a deployment plan with explicit authorization gates
- leave SSH execution behind a service boundary for later approval-driven execution

## Hackathon Positioning

ModelOps AI is being built as an OKX.AI Software Utility ASP. The MVP helps users turn a deployment request into a structured, reviewable model-serving plan.

Current MVP scope:

- OS target: Ubuntu 24.04
- Inference engines: Ollama and vLLM
- Model families: Qwen, Llama, Gemma, and DeepSeek
- Execution mode: dry-run planning first, remote execution only after explicit authorization
- Deployment artifact: generated `generated/deploy.sh` for user review
- Verification: structured post-deploy checks for service health, model availability, and inference response
- Approval gate: `POST /api/v1/deployments/execute` requires `authorized=true` or a valid approval token
- Compact execution history: `GET /api/v1/deployments/{deployment_id}/history`
- Public API protection: production deployments require `X-API-Key` on operational endpoints

## Project Layout

```text
app/
  api/          FastAPI routers
  core/         configuration and logging
  models/       internal domain models
  schemas/      request/response schemas
  services/     planner, analyzer, selector, executor, verifier
  utils/        small shared helpers
tests/          standard-library unittest tests
docs/           architecture notes
```

## Setup

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

```powershell
uvicorn app.main:app --reload
```

Then open:

- `GET http://127.0.0.1:8000/health`
- `POST http://127.0.0.1:8000/api/v1/chat`
- `POST http://127.0.0.1:8000/api/v1/deployments/plan`
- `GET http://127.0.0.1:8000/api/v1/demo/walkthrough`

In production, set `MODEL_OPS_API_KEY` and include it as `X-API-Key` on every endpoint except `/health`. Copy [.env.example](C:/Users/user/Documents/modelops-ai/.env.example) before deploying.

## Deploy

```powershell
# Update MODEL_OPS_API_KEY and EXECUTION_APPROVAL_TOKEN in .env.
# For a new checkout, start from .env.example.
docker compose up --build -d
```

The container listens on port `8000` and stores SQLite data in a Docker volume. See [docs/asp-submission.md](C:/Users/user/Documents/modelops-ai/docs/asp-submission.md) for the public deployment and OKX.AI listing checklist.

For the fastest hosted path, use [render.yaml](C:/Users/user/Documents/modelops-ai/render.yaml) and the launch steps in [docs/go-live.md](C:/Users/user/Documents/modelops-ai/docs/go-live.md).

For a self-managed Ubuntu VPS with automatic HTTPS, use [docker-compose.vps.yml](C:/Users/user/Documents/modelops-ai/docker-compose.vps.yml) and [docs/vps-deploy.md](C:/Users/user/Documents/modelops-ai/docs/vps-deploy.md).

## Test

```powershell
python -m unittest discover -s tests
```

## Deployment Brain

The planning flow is deterministic Python today:

```text
User Request
  -> Model Catalog
  -> Intent Parser
  -> Hardware Analyzer
  -> Engine Recommendation
  -> Deployment Planner
  -> Ollama/vLLM Template
  -> deploy.sh Generator
  -> SSH Executor
  -> Deployment Verifier
```

This gives the future OKX.AI-facing agent a reliable core for selecting Ollama or vLLM based on model metadata, RAM, GPU availability, and GPU memory.

Planner responses include structured commands and a generated Bash script path. The generated script is intentionally ignored by Git because it is an execution artifact produced from the latest plan. The verifier can then check Ollama or OpenAI-compatible vLLM deployments after execution.

The `/chat` endpoint now uses a deterministic intent parser so plain-language prompts can either produce a plan directly or route the user toward approval and execution.

The canonical OKX.AI demo path is available at `GET /api/v1/demo/walkthrough` and documented in [docs/demo-path.md](C:/Users/user/Documents/modelops-ai/docs/demo-path.md).

The recording script is in [docs/demo-script.md](C:/Users/user/Documents/modelops-ai/docs/demo-script.md).
