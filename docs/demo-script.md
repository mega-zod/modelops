# 90-Second Demo Script

Open with the live API or an API client. Keep the camera on the result, not source code.

## 0-15 seconds: The Request

"ModelOps AI turns an open-model request into a safe, verifiable deployment. I will deploy Qwen 3 8B to this Ubuntu host with 32 GB RAM."

Call `POST /api/v1/chat` with the deployment request, or call `POST /api/v1/deployments/plan` directly. Show the engine choice, the generated commands, and the deployment id.

## 15-35 seconds: The Agent Decision

"The agent matched the model catalog to the hardware, selected Ollama, created a reviewable deployment script, and saved the plan. Nothing remote has executed yet."

Call `GET /api/v1/deployments/{deployment_id}`. Point out the risk, reasoning, script, and `no executions yet` status line.

## 35-60 seconds: Explicit Approval

"Execution is gated. The plan only runs after explicit authorization, which keeps deployment control with the operator."

Call `POST /api/v1/deployments/execute` with the saved deployment id, SSH connection details, and `authorized: true`. Use a controlled test host for the recording.

## 60-80 seconds: Verification

"After execution, ModelOps AI checks that the inference service is running, that the model is present, and that the endpoint responds."

Show the returned verification report, then call `GET /api/v1/deployments/{deployment_id}/history`.

## 80-90 seconds: Close

"This is agent-native model operations: plan, approve, execute, verify, and retain an auditable history."
