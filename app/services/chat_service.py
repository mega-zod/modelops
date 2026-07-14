from app.models.deployment import DeploymentRecord, HardwareProfile
from app.models.intent import IntentType
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.deployment import DeploymentPlanRequest, DeploymentPlanResponse
from app.services.deployment_repository import DeploymentRepository
from app.services.deployment_planner import DeploymentPlanner
from app.services.intent_parser import IntentParser


class ChatService:
    def __init__(
        self,
        deployment_planner: DeploymentPlanner | None = None,
        intent_parser: IntentParser | None = None,
        repository: DeploymentRepository | None = None,
    ) -> None:
        self.deployment_planner = deployment_planner or DeploymentPlanner()
        self.intent_parser = intent_parser or IntentParser()
        self.repository = repository or DeploymentRepository()

    def handle(self, request: ChatRequest) -> ChatResponse:
        if request.deployment is not None:
            plan = self.deployment_planner.create_plan(request.deployment)
            return ChatResponse(
                message=(
                    "I created a deployment plan. Remote commands are staged behind "
                    "an authorization step before anything runs."
                ),
                session_id=request.session_id,
                intent="deployment_plan",
                deployment_id=plan.deployment_id,
                status_line=self._plan_status_line(plan),
                deployment_plan=plan,
                execution_history=[],
                suggested_actions=["review_plan", "authorize_execution", "adjust_hardware_or_model"],
            )

        if self._is_latest_lookup_request(request.message):
            record = self.repository.get_latest_record()
            if record is None:
                return ChatResponse(
                    message="I do not have any saved deployments yet.",
                    session_id=request.session_id,
                    intent="deployment_lookup",
                    missing_fields=["deployment"],
                    execution_history=[],
                    suggested_actions=["create_plan", "deploy_a_model"],
                )

            return ChatResponse(
                message=(
                    f"The latest deployment is {record.deployment_id} for "
                    f"{record.plan.model_name} on {record.plan.target_host}."
                ),
                session_id=request.session_id,
                intent="deployment_lookup",
                deployment_id=record.deployment_id,
                status_line=record.status_line,
                deployment_record=record,
                deployment_plan=self._to_plan_response(record),
                execution_history=record.execution_history,
                parsed_intent=None,
                suggested_actions=["review_plan", "execute_existing_plan", "inspect_history"],
            )

        if request.deployment_id is not None:
            record = self.repository.get_record(request.deployment_id)
            if record is None:
                return ChatResponse(
                    message=f"No stored deployment was found for id {request.deployment_id}.",
                    session_id=request.session_id,
                    intent="deployment_lookup",
                    deployment_id=request.deployment_id,
                    status_line=f"No stored deployment was found for id {request.deployment_id}.",
                    missing_fields=["deployment_id"],
                    suggested_actions=["create_plan", "provide_deployment_id"],
                )

            return ChatResponse(
                message=(
                    f"Loaded deployment {record.deployment_id} with "
                    f"{len(record.executions)} execution record(s)."
                ),
                session_id=request.session_id,
                intent="deployment_lookup",
                deployment_id=record.deployment_id,
                status_line=record.status_line,
                deployment_record=record,
                deployment_plan=self._to_plan_response(record),
                execution_history=record.execution_history,
                parsed_intent=None,
                suggested_actions=["review_plan", "execute_existing_plan", "inspect_history"],
            )

        parsed = self.intent_parser.parse(request.message)

        if (
            parsed.intent == IntentType.deployment_request
            and parsed.model_name
            and parsed.target_host
            and parsed.memory_gb is not None
        ):
            deployment_request = DeploymentPlanRequest(
                model_name=parsed.model_name,
                target_host=parsed.target_host,
                hardware=HardwareProfile(
                    cpu_cores=parsed.cpu_cores or 8,
                    memory_gb=parsed.memory_gb,
                    gpu_count=parsed.gpu_count or 0,
                    gpu_memory_gb=parsed.gpu_memory_gb,
                ),
            )
            plan = self.deployment_planner.create_plan(deployment_request)
            return ChatResponse(
                message=(
                    "I parsed your request and created a deployment plan. "
                    "Review the generated script, then authorize execution."
                ),
                session_id=request.session_id,
                intent=parsed.intent.value,
                deployment_id=plan.deployment_id,
                status_line=self._plan_status_line(plan),
                deployment_plan=plan,
                execution_history=[],
                parsed_intent=parsed,
                suggested_actions=["review_plan", "authorize_execution", "run_deployment"],
            )

        if parsed.intent == IntentType.execution_request:
            return ChatResponse(
                message=(
                    "I detected an execution request, but I still need an approved deployment plan. "
                    "Create the plan first, then call the execution endpoint with authorization."
                ),
                session_id=request.session_id,
                intent=parsed.intent.value,
                parsed_intent=parsed,
                missing_fields=["deployment_plan", "authorization"],
                status_line="Execution requested, but no approved plan is loaded yet.",
                execution_history=[],
                suggested_actions=["create_plan", "authorize_execution", "submit_execution_request"],
            )

        if parsed.intent == IntentType.deployment_request:
            return ChatResponse(
                message=(
                    "I can turn that into a deployment plan, but I still need the missing hardware "
                    "details to make the plan concrete."
                ),
                session_id=request.session_id,
                intent=parsed.intent.value,
                parsed_intent=parsed,
                missing_fields=[
                    field
                    for field, present in (
                        ("model_name", parsed.model_name is not None),
                        ("target_host", parsed.target_host is not None),
                        ("memory_gb", parsed.memory_gb is not None),
                    )
                    if not present
                ],
                status_line="Deployment request received, waiting on complete hardware details.",
                execution_history=[],
                suggested_actions=["provide_model_name", "provide_target_host", "provide_hardware_profile"],
            )

        return ChatResponse(
            message=(
                "Tell me the model, target host, and hardware profile and I can produce "
                "a deployment plan with verification steps."
            ),
            session_id=request.session_id,
            intent=parsed.intent.value,
            parsed_intent=parsed,
            missing_fields=[
                field
                for field, present in (
                    ("model_name", parsed.model_name is not None),
                    ("target_host", parsed.target_host is not None),
                    ("memory_gb", parsed.memory_gb is not None),
                )
                if not present
            ],
            status_line="No deployment target yet; waiting for a model, host, and hardware profile.",
            execution_history=[],
            suggested_actions=["provide_model_name", "provide_target_host", "provide_hardware_profile"],
        )

    def _to_plan_response(self, record: DeploymentRecord) -> DeploymentPlanResponse:
        return DeploymentPlanResponse(
            deployment_id=record.deployment_id,
            plan=record.plan,
            authorization_required=any(command.requires_authorization for command in record.plan.commands),
            next_action=(
                "Review the stored plan and authorize execution."
                if not record.executions
                else "Open the execution history or run the plan again."
            ),
        )

    def _is_latest_lookup_request(self, message: str) -> bool:
        lowered = message.lower()
        return any(
            phrase in lowered
            for phrase in (
                "latest deployment",
                "show latest",
                "show me the latest",
                "most recent deployment",
                "latest run",
            )
        )

    def _plan_status_line(self, plan: DeploymentPlanResponse) -> str:
        return f"{plan.plan.model_name} on {plan.plan.target_host}: plan saved, no executions yet."
