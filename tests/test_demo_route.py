import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.models.deployment import DeploymentPlan, DeploymentRisk
from app.services.deployment_repository import DeploymentRepository


class DemoRouteTests(unittest.TestCase):
    def test_walkthrough_exposes_canonical_flow_and_latest_deployment(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = DeploymentRepository(db_path=Path(tmpdir) / "deployments.db")
            record = repo.save_plan(
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

            with patch("app.api.routes.demo.DeploymentRepository", return_value=repo):
                response = TestClient(app).get("/api/v1/demo/walkthrough")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual([step["name"] for step in payload["steps"]], [
            "Create plan",
            "Load by id",
            "Approve and execute",
            "Verify",
        ])
        self.assertTrue(payload["steps"][2]["authorization_required"])
        self.assertEqual(payload["latest_deployment"]["deployment_id"], record.deployment_id)
        self.assertIn(record.deployment_id, payload["next_action"])


if __name__ == "__main__":
    unittest.main()
