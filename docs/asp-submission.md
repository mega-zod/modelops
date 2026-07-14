# ModelOps AI ASP Submission

## Product

**Name:** ModelOps AI

**Category:** Software Utility

**One-line description:** An agent that turns a model-serving request into a hardware-aware deployment plan, an explicitly approved SSH execution, and a verified inference service.

## User Value

ModelOps AI reduces the operational work between choosing an open model and running it safely. It assesses available hardware, selects Ollama or vLLM, produces reviewable commands and a deployment script, requires explicit approval before remote execution, then verifies the resulting inference endpoint.

## Public Service Contract

Host the service on a public HTTPS domain, then provide these details in the listing:

- Base URL: `https://YOUR-DOMAIN/api/v1`
- Authentication: `X-API-Key: YOUR_MODEL_OPS_API_KEY`
- Health check: `GET /health` (intentionally public)
- Agent entry point: `POST /chat`
- Demo guide: `GET /demo/walkthrough` with `X-API-Key`

## Core Demo Calls

1. `POST /deployments/plan` to create the plan.
2. `GET /deployments/{deployment_id}` to load it by id.
3. `POST /deployments/execute` with explicit authorization to run it.
4. `GET /deployments/{deployment_id}/history` to show execution and verification history.

## Deployment Checklist

1. Copy `.env.example` to `.env` and replace both secret placeholders with long, unique values.
2. Start the service with `docker compose up --build -d`.
3. Put the service behind HTTPS through the selected hosting provider or reverse proxy.
4. Confirm `GET https://YOUR-DOMAIN/health` returns `200`.
5. Confirm operational endpoints reject requests without `X-API-Key`.
6. Use `/api/v1/demo/walkthrough` with `X-API-Key` while recording the submission video.

Do not expose SSH passwords, private keys, approval tokens, or the contents of `.env` in the listing or demo.
