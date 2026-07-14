import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.models.deployment import (
    CommandExecutionResult,
    DeploymentExecutionReport,
    DeploymentPlan,
    DeploymentRisk,
    ExecutionStatus,
)


class DeploymentRouteTests(unittest.TestCase):
    def test_execute_rejects_unapproved_requests(self) -> None:
        response = TestClient(app).post(
            "/api/v1/deployments/execute",
            json={
                "plan": self._plan_payload(),
                "authorized": False,
                "ssh_username": "ubuntu",
            },
        )

        self.assertEqual(response.status_code, 403)

    def test_execute_returns_report_when_service_allows_execution(self) -> None:
        fake_service = MagicMock()
        fake_service.execute.return_value = DeploymentExecutionReport(
            plan=self._plan(),
            authorized=True,
            execution_status=ExecutionStatus.succeeded,
            message="Deployment executed and verified successfully.",
            next_action="No immediate action required.",
            command_results=[
                CommandExecutionResult(command="echo ready", exit_code=0, stdout="ready", stderr=""),
            ],
        )

        with patch("app.api.routes.deployments.DeploymentExecutionService", return_value=fake_service):
            response = TestClient(app).post(
                "/api/v1/deployments/execute",
                json={
                    "plan": self._plan_payload(),
                    "authorized": True,
                    "ssh_username": "ubuntu",
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["execution_status"], "succeeded")
        self.assertEqual(payload["command_results"][0]["exit_code"], 0)

    def test_list_and_get_return_persisted_deployment(self) -> None:
        create_response = TestClient(app).post(
            "/api/v1/deployments/plan",
            json={
                "model_name": "qwen3:8b",
                "target_host": "gpu-node-01",
                "hardware": {
                    "cpu_cores": 8,
                    "memory_gb": 32,
                    "gpu_count": 0,
                },
            },
        )
        self.assertEqual(create_response.status_code, 200)
        deployment_id = create_response.json()["deployment_id"]

        list_response = TestClient(app).get("/api/v1/deployments")
        self.assertEqual(list_response.status_code, 200)
        items = list_response.json()["items"]
        self.assertTrue(any(item["deployment_id"] == deployment_id for item in items))

        detail_response = TestClient(app).get(f"/api/v1/deployments/{deployment_id}")
        self.assertEqual(detail_response.status_code, 200)
        detail = detail_response.json()["record"]
        self.assertEqual(detail["deployment_id"], deployment_id)
        self.assertEqual(detail["plan"]["deployment_id"], deployment_id)
        self.assertEqual(detail["executions"], [])
        self.assertEqual(detail_response.json()["execution_history"], [])
        self.assertIn("no executions yet", detail["status_line"])

    def test_history_endpoint_returns_compact_execution_summary(self) -> None:
        from app.services.deployment_repository import DeploymentRepository
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            repo = DeploymentRepository(db_path=Path(tmpdir) / "deployments.db")
            stored = repo.save_plan(self._plan())
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

            with patch("app.api.routes.deployments.DeploymentRepository", return_value=repo):
                response = TestClient(app).get(f"/api/v1/deployments/{stored.deployment_id}/history")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["deployment_id"], stored.deployment_id)
        self.assertEqual(len(payload["execution_history"]), 1)
        self.assertEqual(payload["execution_history"][0]["runtime"], "ollama")
        self.assertEqual(payload["execution_history"][0]["command_count"], 1)
        self.assertIn("last run succeeded", payload["execution_history"][0]["status_line"])

    def _plan(self) -> DeploymentPlan:
        return DeploymentPlan(
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

    def _plan_payload(self) -> dict[str, object]:
        return self._plan().model_dump()


if __name__ == "__main__":
    unittest.main()
