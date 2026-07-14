import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.models.deployment import (
    CommandExecutionResult,
    DeploymentExecutionReport,
    DeploymentPlan,
    DeploymentRisk,
    ExecutionStatus,
)
from app.services.chat_service import ChatService
from app.services.deployment_repository import DeploymentRepository


class ChatEndpointTests(unittest.TestCase):
    def test_chat_collects_requirements_without_deployment_payload(self) -> None:
        response = TestClient(app).post("/api/v1/chat", json={"message": "deploy a model"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["intent"], "deployment_request")
        self.assertEqual(
            sorted(payload["missing_fields"]),
            ["memory_gb", "model_name", "target_host"],
        )
        self.assertIn("provide_model_name", payload["suggested_actions"])

    def test_chat_returns_deployment_plan(self) -> None:
        response = TestClient(app).post(
            "/api/v1/chat",
            json={
                "message": "deploy llama",
                "deployment": {
                    "model_name": "llama-3.1-8b",
                    "target_host": "gpu-node-01",
                    "hardware": {
                        "cpu_cores": 16,
                        "memory_gb": 64,
                        "gpu_count": 1,
                        "gpu_memory_gb": 24,
                    },
                },
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["intent"], "deployment_plan")
        self.assertEqual(payload["deployment_plan"]["plan"]["risk"], "low")

    def test_chat_detects_execution_request(self) -> None:
        response = TestClient(app).post("/api/v1/chat", json={"message": "execute the deployment now"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["intent"], "execution_request")
        self.assertIn("deployment_plan", payload["missing_fields"])

    def test_chat_parses_plain_language_deployment_request(self) -> None:
        response = TestClient(app).post(
            "/api/v1/chat",
            json={
                "message": "deploy llama3.1:8b on gpu-node-01 with 64 gb ram and 1 gpu",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["intent"], "deployment_request")
        self.assertIsNotNone(payload["deployment_plan"])
        self.assertEqual(payload["deployment_plan"]["plan"]["runtime"], "ollama")
        self.assertEqual(payload["parsed_intent"]["target_host"], "gpu-node-01")

    def test_chat_loads_existing_deployment_by_id(self) -> None:
        create_response = TestClient(app).post(
            "/api/v1/chat",
            json={
                "message": "deploy qwen3:8b on gpu-node-01 with 32 gb ram",
                "deployment": {
                    "model_name": "qwen3:8b",
                    "target_host": "gpu-node-01",
                    "hardware": {
                        "cpu_cores": 8,
                        "memory_gb": 32,
                        "gpu_count": 0,
                    },
                },
            },
        )
        deployment_id = create_response.json()["deployment_id"]

        response = TestClient(app).post(
            "/api/v1/chat",
            json={"message": "show me that deployment", "deployment_id": deployment_id},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["intent"], "deployment_lookup")
        self.assertEqual(payload["deployment_id"], deployment_id)
        self.assertEqual(payload["deployment_record"]["deployment_id"], deployment_id)
        self.assertEqual(payload["deployment_plan"]["plan"]["deployment_id"], deployment_id)

    def test_chat_loads_execution_history_by_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = DeploymentRepository(db_path=Path(tmpdir) / "deployments.db")
            stored = repo.save_plan(
                DeploymentPlan(
                    model_name="qwen3:8b",
                    target_host="gpu-node-01",
                    runtime="ollama",
                    port=11434,
                    risk=DeploymentRisk.low,
                    reason="test",
                    summary="test",
                    commands=[],
                    verification_steps=[],
                )
            )
            repo.save_execution(
                stored.deployment_id,
                DeploymentExecutionReport(
                    deployment_id=stored.deployment_id,
                    execution_id=None,
                    plan=stored.plan,
                    authorized=True,
                    execution_status=ExecutionStatus.succeeded,
                    message="Deployment executed and verified successfully.",
                    next_action="No immediate action required.",
                    command_results=[
                        CommandExecutionResult(command="echo ready", exit_code=0, stdout="ready", stderr=""),
                    ],
                ),
            )

            service = ChatService(repository=repo)
            with patch("app.api.routes.chat.ChatService", return_value=service):
                response = TestClient(app).post(
                    "/api/v1/chat",
                    json={"message": "show me history", "deployment_id": stored.deployment_id},
                )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["intent"], "deployment_lookup")
        self.assertEqual(payload["deployment_id"], stored.deployment_id)
        self.assertEqual(len(payload["execution_history"]), 1)
        self.assertEqual(payload["execution_history"][0]["execution_status"], "succeeded")
        self.assertEqual(payload["execution_history"][0]["command_count"], 1)
        self.assertIn("last run succeeded", payload["status_line"])

    def test_chat_returns_latest_deployment_shortcut(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = DeploymentRepository(db_path=Path(tmpdir) / "deployments.db")
            first = repo.save_plan(
                DeploymentPlan(
                    model_name="qwen3:8b",
                    target_host="gpu-node-01",
                    runtime="ollama",
                    port=11434,
                    risk=DeploymentRisk.low,
                    reason="test",
                    summary="test",
                    commands=[],
                    verification_steps=[],
                )
            )
            latest = repo.save_plan(
                DeploymentPlan(
                    model_name="llama3.1:8b",
                    target_host="gpu-node-02",
                    runtime="ollama",
                    port=11434,
                    risk=DeploymentRisk.low,
                    reason="test",
                    summary="test",
                    commands=[],
                    verification_steps=[],
                )
            )

            service = ChatService(repository=repo)
            with patch("app.api.routes.chat.ChatService", return_value=service):
                response = TestClient(app).post(
                    "/api/v1/chat",
                    json={"message": "show me the latest deployment"},
                )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["intent"], "deployment_lookup")
        self.assertEqual(payload["deployment_id"], latest.deployment_id)
        self.assertEqual(payload["deployment_record"]["deployment_id"], latest.deployment_id)
        self.assertEqual(payload["deployment_plan"]["plan"]["model_name"], "llama3.1:8b")
        self.assertEqual(payload["execution_history"], [])
        self.assertIn("no executions yet", payload["status_line"])
        self.assertNotEqual(first.deployment_id, latest.deployment_id)


if __name__ == "__main__":
    unittest.main()
