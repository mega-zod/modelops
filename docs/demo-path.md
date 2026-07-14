# OKX.AI Demo Path

This is the canonical demo path for ModelOps AI.

Start with `GET /api/v1/demo/walkthrough` to display the current demo state and the exact API sequence. It includes the latest saved deployment when one exists.

## Flow

1. Create a deployment plan from chat or `POST /api/v1/deployments/plan`.
2. Load the plan by id with `GET /api/v1/deployments/{deployment_id}` or by asking chat for the deployment id.
3. Review the plan, then approve it by sending `POST /api/v1/deployments/execute` with `authorized=true` or the approval token.
4. Execute the plan over SSH.
5. Verify the deployment from the returned verification report.

## Demo Promise

- The planner stays deterministic.
- The execution step is explicitly gated.
- The operator can inspect compact execution history at `GET /api/v1/deployments/{deployment_id}/history`.
- Chat lookups return the same compact history so the flow works in both API-first and conversational demos.

## Suggested Talking Track

1. "I asked for a deployment in plain language."
2. "The agent resolved the model catalog and generated a reviewable plan."
3. "I loaded the saved deployment by id and checked the history."
4. "I approved execution."
5. "The agent executed the commands and verified the service."
