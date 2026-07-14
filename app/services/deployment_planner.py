from app.models.deployment import DeploymentPlan, InferenceEngine
from app.schemas.deployment import DeploymentPlanRequest, DeploymentPlanResponse
from app.services.deployment_templates import DeploymentTemplateRegistry
from app.services.hardware_analyzer import HardwareAnalyzer
from app.services.deployment_repository import DeploymentRepository
from app.services.model_catalog import recommend_inference_engine
from app.services.model_selector import ModelSelector
from app.services.script_generator import DeploymentScriptGenerator


class DeploymentPlanner:
    def __init__(
        self,
        model_selector: ModelSelector | None = None,
        hardware_analyzer: HardwareAnalyzer | None = None,
        template_registry: DeploymentTemplateRegistry | None = None,
        script_generator: DeploymentScriptGenerator | None = None,
        repository: DeploymentRepository | None = None,
    ) -> None:
        self.model_selector = model_selector or ModelSelector()
        self.hardware_analyzer = hardware_analyzer or HardwareAnalyzer()
        self.template_registry = template_registry or DeploymentTemplateRegistry()
        self.script_generator = script_generator or DeploymentScriptGenerator()
        self.repository = repository or DeploymentRepository()

    def create_plan(self, request: DeploymentPlanRequest) -> DeploymentPlanResponse:
        model = self.model_selector.select(request.model_name)
        recommendation = recommend_inference_engine(model, request.hardware)
        risk, warnings = self.hardware_analyzer.assess(request.hardware, model)
        warnings.extend(recommendation.warnings)
        port = request.desired_port or self._default_port_for_engine(recommendation.engine)

        commands = self.template_registry.build_commands(recommendation.engine, model.name, port)
        verification_steps = [
            f"Check that port {port} is listening.",
            f"Call http://{request.target_host}:{port}/health.",
            "Send a small inference request and validate latency and response shape.",
        ]
        script = self.script_generator.generate(
            model_name=model.name,
            engine=recommendation.engine.value,
            target_host=request.target_host,
            port=port,
            commands=commands,
            verification_steps=verification_steps,
        )

        plan = DeploymentPlan(
            deployment_id=None,
            model_name=model.name,
            target_host=request.target_host,
            runtime=recommendation.engine.value,
            port=port,
            risk=risk,
            reason=recommendation.reason,
            prerequisites=[
                "Ubuntu 24.04 host",
                "Docker installed and running",
                "Network access to pull runtime images",
            ],
            summary=(
                f"Deploy {model.name} to {request.target_host} with "
                f"{recommendation.engine} on port {port}."
            ),
            commands=commands,
            verification_steps=verification_steps,
            script=script,
            warnings=warnings,
        )
        stored_record = self.repository.save_plan(plan)
        plan = stored_record.plan

        return DeploymentPlanResponse(
            deployment_id=plan.deployment_id,
            plan=plan,
            authorization_required=any(command.requires_authorization for command in commands),
            next_action=(
                "Review the plan and authorize execution."
                if request.execution_mode == "dry_run"
                else "Execution can proceed through the SSH executor."
            ),
        )

    def _default_port_for_engine(self, engine: InferenceEngine) -> int:
        if engine == InferenceEngine.ollama:
            return 11434
        if engine == InferenceEngine.vllm:
            return 8000
        return 8000
