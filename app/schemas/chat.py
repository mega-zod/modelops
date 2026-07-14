from pydantic import BaseModel, Field

from app.models.deployment import DeploymentRecord
from app.models.deployment import ExecutionHistoryItem
from app.models.intent import IntentClassification
from app.schemas.deployment import DeploymentPlanRequest, DeploymentPlanResponse


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: str | None = Field(default=None, max_length=128)
    deployment_id: str | None = Field(default=None, max_length=128)
    deployment: DeploymentPlanRequest | None = None


class ChatResponse(BaseModel):
    message: str
    session_id: str | None = None
    intent: str
    deployment_id: str | None = None
    status_line: str | None = None
    deployment_plan: DeploymentPlanResponse | None = None
    deployment_record: DeploymentRecord | None = None
    execution_history: list[ExecutionHistoryItem] = Field(default_factory=list)
    parsed_intent: IntentClassification | None = None
    missing_fields: list[str] = Field(default_factory=list)
    suggested_actions: list[str] = Field(default_factory=list)
