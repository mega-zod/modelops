from fastapi import APIRouter, HTTPException, Query

from app.schemas.deployment import (
    DeploymentExecuteRequest,
    DeploymentExecuteResponse,
    DeploymentDetailResponse,
    DeploymentHistoryResponse,
    DeploymentListResponse,
    DeploymentPlanRequest,
    DeploymentPlanResponse,
)
from app.services.deployment_repository import DeploymentRepository
from app.services.deployment_executor import DeploymentExecutionService
from app.services.deployment_planner import DeploymentPlanner

router = APIRouter()


@router.post("/plan", response_model=DeploymentPlanResponse)
def create_plan(request: DeploymentPlanRequest) -> DeploymentPlanResponse:
    return DeploymentPlanner().create_plan(request)


@router.post("/execute", response_model=DeploymentExecuteResponse)
def execute(request: DeploymentExecuteRequest) -> DeploymentExecuteResponse:
    try:
        return DeploymentExecutionService().execute(request)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc


@router.get("", response_model=DeploymentListResponse)
def list_deployments(limit: int = Query(default=50, ge=1, le=200)) -> DeploymentListResponse:
    return DeploymentListResponse(items=DeploymentRepository().list_deployments(limit=limit))


@router.get("/{deployment_id}", response_model=DeploymentDetailResponse)
def get_deployment(deployment_id: str) -> DeploymentDetailResponse:
    record = DeploymentRepository().get_record(deployment_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Deployment {deployment_id} was not found.")
    return DeploymentDetailResponse(record=record, execution_history=record.execution_history)


@router.get("/{deployment_id}/history", response_model=DeploymentHistoryResponse)
def get_deployment_history(deployment_id: str) -> DeploymentHistoryResponse:
    record = DeploymentRepository().get_record(deployment_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Deployment {deployment_id} was not found.")
    return DeploymentHistoryResponse(deployment_id=deployment_id, execution_history=record.execution_history)
