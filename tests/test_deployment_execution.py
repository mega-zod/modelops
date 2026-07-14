import os
import unittest
from unittest.mock import MagicMock, patch

from app.core.config import get_settings
from app.models.deployment import (
    CommandExecutionResult,
    DeploymentPlan,
    DeploymentRisk,
    DeploymentVerificationReport,
    ExecutionStatus,
    VerificationCheck,
    VerificationStatus,
)
from app.schemas.deployment import DeploymentExecuteRequest
from app.services.deployment_executor import DeploymentExecutionService


class DeploymentExecutionServiceTests(unittest.TestCase):
    def test_requires_authorization(self) -> None:
        service = DeploymentExecutionService()
        request = self._request(authorized=False, approval_token=None)

        with self.assertRaises(PermissionError):
            service.execute(request)

    def test_executes_and_verifies_when_authorized(self) -> None:
        ssh_executor = MagicMock()
        ssh_executor.execute.return_value = [
            CommandExecutionResult(command="echo ready", exit_code=0, stdout="ready", stderr=""),
        ]

        verifier = MagicMock()
        verifier.verify.return_value = DeploymentVerificationReport(
            model_name="qwen3:8b",
            target_host="gpu-node-01",
            runtime="ollama",
            port=11434,
            success=True,
            checks=[
                VerificationCheck(
                    name="service_running",
                    status=VerificationStatus.passed,
                    detail="ok",
                )
            ],
        )

        service = DeploymentExecutionService(ssh_executor=ssh_executor, verifier=verifier)
        report = service.execute(self._request(authorized=True))

        self.assertEqual(report.execution_status, ExecutionStatus.succeeded)
        self.assertTrue(report.authorized)
        self.assertTrue(report.verification_report.success)
        self.assertEqual(report.command_results[0].exit_code, 0)

    def test_executes_with_approval_token(self) -> None:
        ssh_executor = MagicMock()
        ssh_executor.execute.return_value = []

        get_settings.cache_clear()
        try:
            with patch.dict(os.environ, {"EXECUTION_APPROVAL_TOKEN": "let-me-run"}):
                get_settings.cache_clear()
                service = DeploymentExecutionService(ssh_executor=ssh_executor, verifier=MagicMock())
                report = service.execute(
                    self._request(authorized=False, approval_token="let-me-run", verify=False)
                )
        finally:
            get_settings.cache_clear()

        self.assertEqual(report.execution_status, ExecutionStatus.succeeded)
        self.assertTrue(report.authorized)

    def test_executes_from_stored_deployment_id(self) -> None:
        from app.services.deployment_repository import DeploymentRepository
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            repo = DeploymentRepository(db_path=Path(tmpdir) / "deployments.db")
            stored = repo.save_plan(self._request(authorized=True).plan)

            ssh_executor = MagicMock()
            ssh_executor.execute.return_value = []

            service = DeploymentExecutionService(ssh_executor=ssh_executor, verifier=MagicMock(), repository=repo)
            report = service.execute(
                DeploymentExecuteRequest(
                    deployment_id=stored.deployment_id,
                    plan=None,
                    authorized=True,
                    ssh_username="ubuntu",
                    verify=False,
                )
            )

        self.assertEqual(report.deployment_id, stored.deployment_id)
        self.assertEqual(report.execution_status, ExecutionStatus.succeeded)

    def _request(
        self,
        authorized: bool,
        approval_token: str | None = None,
        verify: bool = True,
    ) -> DeploymentExecuteRequest:
        return DeploymentExecuteRequest(
            plan=DeploymentPlan(
                model_name="qwen3:8b",
                target_host="gpu-node-01",
                runtime="ollama",
                port=11434,
                risk=DeploymentRisk.low,
                reason="test",
                summary="test",
                commands=[],
                verification_steps=[],
            ),
            authorized=authorized,
            approval_token=approval_token,
            ssh_username="ubuntu",
            verify=verify,
        )


if __name__ == "__main__":
    unittest.main()
