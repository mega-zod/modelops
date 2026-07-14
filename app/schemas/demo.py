from pydantic import BaseModel, Field

from app.models.deployment import DeploymentSummary


class DemoStep(BaseModel):
    order: int
    name: str
    method: str
    endpoint: str
    purpose: str
    authorization_required: bool = False


class DemoWalkthroughResponse(BaseModel):
    title: str = "ModelOps AI OKX.AI Demo"
    steps: list[DemoStep] = Field(default_factory=list)
    latest_deployment: DeploymentSummary | None = None
    next_action: str
