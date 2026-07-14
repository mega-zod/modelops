from pydantic import BaseModel, Field

from app.models.deployment import (
    DeploymentExecutionReport,
    DeploymentPlan,
    DeploymentRecord,
    DeploymentSummary,
    ExecutionHistoryItem,
    ExecutionMode,
    HardwareProfile,
)


class DeploymentPlanRequest(BaseModel):
    model_name: str = Field(min_length=1, examples=["llama-3.1-8b"])
    target_host: str = Field(min_length=1, examples=["gpu-node-01.example.com"])
    hardware: HardwareProfile
    execution_mode: ExecutionMode = ExecutionMode.dry_run
    desired_port: int | None = Field(default=None, ge=1, le=65535)
    notes: str | None = Field(default=None, max_length=2000)


class DeploymentPlanResponse(BaseModel):
    deployment_id: str | None = None
    plan: DeploymentPlan
    authorization_required: bool
    next_action: str


class DeploymentExecuteRequest(BaseModel):
    deployment_id: str | None = Field(default=None, max_length=128)
    plan: DeploymentPlan | None = None
    authorized: bool = False
    approval_token: str | None = Field(default=None, max_length=256)
    ssh_username: str = Field(min_length=1, max_length=128)
    ssh_password: str | None = Field(default=None, max_length=256)
    ssh_key_filename: str | None = Field(default=None, max_length=512)
    ssh_port: int = Field(default=22, ge=1, le=65535)
    verify: bool = True


class DeploymentExecuteResponse(DeploymentExecutionReport):
    pass


class DeploymentListResponse(BaseModel):
    items: list[DeploymentSummary]


class DeploymentDetailResponse(BaseModel):
    record: DeploymentRecord
    execution_history: list[ExecutionHistoryItem] = Field(default_factory=list)


class DeploymentHistoryResponse(BaseModel):
    deployment_id: str
    execution_history: list[ExecutionHistoryItem] = Field(default_factory=list)
