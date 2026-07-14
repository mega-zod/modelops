from enum import StrEnum

from pydantic import BaseModel, Field


class IntentType(StrEnum):
    deployment_request = "deployment_request"
    execution_request = "execution_request"
    clarification_request = "clarification_request"
    general_question = "general_question"


class IntentClassification(BaseModel):
    intent: IntentType
    confidence: float = Field(ge=0.0, le=1.0)
    model_name: str | None = None
    target_host: str | None = None
    cpu_cores: int | None = None
    memory_gb: float | None = None
    gpu_count: int | None = None
    gpu_memory_gb: float | None = None
    assumptions: list[str] = Field(default_factory=list)
    signals: list[str] = Field(default_factory=list)
