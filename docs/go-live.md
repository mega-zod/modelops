# Go Live

This repo is ready for a public FastAPI deployment. The fastest path is Render using the included [render.yaml](C:/Users/user/Documents/modelops-ai/render.yaml).

## Recommended path

1. Push this repo to GitHub.
2. In Render, create a new Blueprint and point it at the repository.
3. When prompted, provide values for:
   - `MODEL_OPS_API_KEY`
   - `EXECUTION_APPROVAL_TOKEN`
4. Let Render create the web service.
5. After the first deploy, add a persistent disk mounted at `/app/data` if you want deployment history and saved plans to survive restarts.
6. Confirm these URLs:
   - `GET https://YOUR-SERVICE.onrender.com/health`
   - `GET https://YOUR-SERVICE.onrender.com/api/v1/demo/walkthrough` with `X-API-Key`

## Why Render

- The app already ships with a `Dockerfile`.
- Render supports Docker web services at a public `onrender.com` URL.
- The included Blueprint sets the health check path and production environment variables.

## Important note about persistence

The service uses SQLite by default. Saved plans, approvals, and execution history live under `/app/data/modelops.db`.

- On Render, persistent disks are available only on paid web services.
- Without a disk, the service still runs, but data can reset on redeploy or restart.

## Smoke test

Use your live URL after deploy:

```bash
curl https://YOUR-SERVICE.onrender.com/health
curl -H "X-API-Key: YOUR_MODEL_OPS_API_KEY" https://YOUR-SERVICE.onrender.com/api/v1/demo/walkthrough
```
