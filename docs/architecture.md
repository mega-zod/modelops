# ModelOps AI Architecture

ModelOps AI is organized as a FastAPI application with a small service layer around a deployment-focused agent workflow.

```text
User
  |
  v
FastAPI API Gateway
  |
  v
Chat / Deployment Router
  |
  v
Planner Service
  |-- Hardware Analyzer
  |-- Model Selector
  |-- Deployment Planner
  |-- SSH Executor
  `-- Verifier
```

## Phases

### Phase 1

- FastAPI app factory
- health endpoint
- chat endpoint
- request validation
- deterministic planning responses

### Phase 2

- richer hardware analysis
- model profile catalog
- deployment planner scoring

### Phase 3

- SSH executor implementation
- explicit user authorization before remote commands
- deployment verification checks

### Phase 4

- OKX.AI integration
- agent listing and task marketplace flow
- authenticated callbacks and audit trail

## Design Notes

- API schemas live separately from internal models.
- Services contain business logic and can be tested without HTTP.
- The SSH executor is intentionally isolated so dangerous operations stay behind authorization checks.
- The initial planner is deterministic; an LLM can later be added behind the same service contract.
