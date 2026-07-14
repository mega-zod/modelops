from app.core.config import get_settings
from app.models.deployment import (
    DeploymentExecutionReport,
    DeploymentPlan,
    ExecutionStatus,
)
from app.schemas.deployment import DeploymentExecuteRequest
from app.services.deployment_repository import DeploymentRepository
from app.services.ssh_executor import SSHConnectionConfig, SSHExecutor
from app.services.verifier import DeploymentVerifier


class DeploymentExecutionService:
    def __init__(
        self,
        ssh_executor: SSHExecutor | None = None,
        verifier: DeploymentVerifier | None = None,
        repository: DeploymentRepository | None = None,
    ) -> None:
        self.ssh_executor = ssh_executor or SSHExecutor()
        self.verifier = verifier or DeploymentVerifier()
        self.repository = repository or DeploymentRepository()

    def execute(self, request: DeploymentExecuteRequest) -> DeploymentExecutionReport:
        self._ensure_authorized(request)
        plan = self._resolve_plan(request)

        connection = SSHConnectionConfig(
            host=plan.target_host,
            username=request.ssh_username,
            port=request.ssh_port,
            password=request.ssh_password,
            key_filename=request.ssh_key_filename,
            timeout_seconds=get_settings().ssh_connect_timeout_seconds,
        )

        command_results = self.ssh_executor.execute(
            connection=connection,
            commands=plan.commands,
            authorized=True,
        )
        execution_success = all(result.exit_code == 0 for result in command_results)

        verification_report = None
        if request.verify and execution_success:
            verification_report = self.verifier.verify(plan)
            execution_success = verification_report.success

        status = ExecutionStatus.succeeded if execution_success else ExecutionStatus.failed
        report = DeploymentExecutionReport(
            plan=plan,
            authorized=True,
            execution_status=status,
            message=(
                "Deployment executed and verified successfully."
                if execution_success
                else "Deployment execution completed, but one or more checks failed."
            ),
            next_action=(
                "No immediate action required."
                if execution_success
                else "Inspect command output and fix the reported failures."
            ),
            script=plan.script,
            command_results=command_results,
            verification_report=verification_report,
        )
        deployment_id = plan.deployment_id or request.deployment_id
        if deployment_id is None:
            raise ValueError("Resolved deployment is missing an id.")
        report = report.model_copy(update={"deployment_id": deployment_id})
        stored_execution = self.repository.save_execution(deployment_id, report)
        return stored_execution.report

    def _ensure_authorized(self, request: DeploymentExecuteRequest) -> None:
        settings = get_settings()
        token_matches = (
            settings.execution_approval_token is not None
            and request.approval_token == settings.execution_approval_token
        )

        if not (request.authorized or token_matches):
            raise PermissionError("Execution requires authorized=true or a valid approval token.")

    def _resolve_plan(self, request: DeploymentExecuteRequest) -> DeploymentPlan:
        if request.plan is not None:
            stored = self.repository.save_plan(request.plan)
            return stored.plan

        if request.deployment_id is None:
            raise ValueError("Either plan or deployment_id must be provided.")

        record = self.repository.get_record(request.deployment_id)
        if record is None:
            raise LookupError(f"Deployment {request.deployment_id} was not found.")
        return record.plan
