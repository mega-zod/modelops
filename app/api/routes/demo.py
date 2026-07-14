from fastapi import APIRouter

from app.schemas.demo import DemoStep, DemoWalkthroughResponse
from app.services.deployment_repository import DeploymentRepository

router = APIRouter()


@router.get("/walkthrough", response_model=DemoWalkthroughResponse)
def get_walkthrough() -> DemoWalkthroughResponse:
    latest = DeploymentRepository().list_deployments(limit=1)
    latest_deployment = latest[0] if latest else None
    next_action = (
        f"Load deployment {latest_deployment.deployment_id}, review it, then explicitly approve execution."
        if latest_deployment is not None
        else "Create a deployment plan to begin the demo."
    )
    return DemoWalkthroughResponse(
        steps=[
            DemoStep(
                order=1,
                name="Create plan",
                method="POST",
                endpoint="/api/v1/deployments/plan",
                purpose="Turn model and hardware requirements into a stored, reviewable plan.",
            ),
            DemoStep(
                order=2,
                name="Load by id",
                method="GET",
                endpoint="/api/v1/deployments/{deployment_id}",
                purpose="Inspect the plan and its compact execution history.",
            ),
            DemoStep(
                order=3,
                name="Approve and execute",
                method="POST",
                endpoint="/api/v1/deployments/execute",
                purpose="Run the approved plan over SSH.",
                authorization_required=True,
            ),
            DemoStep(
                order=4,
                name="Verify",
                method="GET",
                endpoint="/api/v1/deployments/{deployment_id}/history",
                purpose="Review execution status and the returned service verification result.",
            ),
        ],
        latest_deployment=latest_deployment,
        next_action=next_action,
    )
