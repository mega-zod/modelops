from enum import StrEnum

from pydantic import BaseModel, Field


class DeploymentRisk(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"


class ExecutionMode(StrEnum):
    dry_run = "dry_run"
    authorized = "authorized"


class InferenceEngine(StrEnum):
    ollama = "ollama"
    vllm = "vllm"
    docker = "docker"


class VerificationStatus(StrEnum):
    passed = "passed"
    failed = "failed"
    skipped = "skipped"


class ExecutionStatus(StrEnum):
    pending = "pending"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    blocked = "blocked"


class HardwareProfile(BaseModel):
    cpu_cores: int = Field(ge=1)
    memory_gb: float = Field(gt=0)
    gpu_count: int = Field(default=0, ge=0)
    gpu_memory_gb: float | None = Field(default=None, gt=0)
    os: str | None = None


class ModelProfile(BaseModel):
    name: str
    family: str = "custom"
    parameter_size_b: float | None = None
    min_memory_gb: float
    min_gpu_memory_gb: float | None = None
    gpu_required: bool = False
    supports_cpu: bool = True
    recommended_runtime: InferenceEngine = InferenceEngine.docker
    default_port: int


class EngineRecommendation(BaseModel):
    engine: InferenceEngine
    reason: str
    warnings: list[str] = Field(default_factory=list)


class PlannedCommand(BaseModel):
    command: str
    description: str
    requires_authorization: bool = True


class DeploymentScript(BaseModel):
    path: str
    shell: str = "bash"
    content: str


class VerificationCheck(BaseModel):
    name: str
    status: VerificationStatus
    detail: str
    url: str | None = None


class DeploymentVerificationReport(BaseModel):
    model_name: str
    target_host: str
    runtime: str
    port: int
    success: bool
    checks: list[VerificationCheck]


class CommandExecutionResult(BaseModel):
    command: str
    exit_code: int
    stdout: str
    stderr: str


class DeploymentPlan(BaseModel):
    deployment_id: str | None = None
    model_name: str
    target_host: str
    runtime: str
    port: int
    risk: DeploymentRisk
    reason: str
    prerequisites: list[str] = Field(default_factory=list)
    summary: str
    commands: list[PlannedCommand]
    verification_steps: list[str]
    script: DeploymentScript | None = None
    warnings: list[str] = Field(default_factory=list)


class DeploymentExecutionReport(BaseModel):
    deployment_id: str | None = None
    execution_id: str | None = None
    plan: DeploymentPlan
    authorized: bool
    execution_status: ExecutionStatus
    message: str
    next_action: str
    script: DeploymentScript | None = None
    command_results: list[CommandExecutionResult] = Field(default_factory=list)
    verification_report: DeploymentVerificationReport | None = None


class DeploymentExecutionEntry(BaseModel):
    execution_id: str
    created_at: str
    report: DeploymentExecutionReport


class ExecutionHistoryItem(BaseModel):
    execution_id: str
    created_at: str
    execution_status: ExecutionStatus
    runtime: str
    port: int
    command_count: int
    command_preview: list[str] = Field(default_factory=list)
    verification_success: bool | None = None
    message: str
    status_line: str | None = None


class DeploymentSummary(BaseModel):
    deployment_id: str
    created_at: str
    updated_at: str
    model_name: str
    target_host: str
    runtime: str
    port: int
    execution_count: int
    last_executed_at: str | None = None
    last_execution_status: ExecutionStatus | None = None
    last_execution_message: str | None = None
    status_line: str | None = None


class DeploymentRecord(BaseModel):
    deployment_id: str
    created_at: str
    updated_at: str
    plan: DeploymentPlan
    executions: list[DeploymentExecutionEntry] = Field(default_factory=list)
    execution_history: list[ExecutionHistoryItem] = Field(default_factory=list)
    status_line: str | None = None
