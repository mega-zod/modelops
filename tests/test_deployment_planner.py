import unittest

from app.models.deployment import HardwareProfile
from app.schemas.deployment import DeploymentPlanRequest
from app.services.deployment_planner import DeploymentPlanner


class DeploymentPlannerTests(unittest.TestCase):
    def test_known_gpu_model_gets_low_risk_plan_on_sufficient_hardware(self) -> None:
        request = DeploymentPlanRequest(
            model_name="llama-3.1-8b",
            target_host="gpu-node-01",
            hardware=HardwareProfile(
                cpu_cores=16,
                memory_gb=64,
                gpu_count=1,
                gpu_memory_gb=24,
            ),
        )

        response = DeploymentPlanner().create_plan(request)

        self.assertEqual(response.plan.runtime, "vllm")
        self.assertEqual(response.plan.risk, "low")
        self.assertTrue(response.authorization_required)

    def test_insufficient_hardware_surfaces_warning(self) -> None:
        request = DeploymentPlanRequest(
            model_name="llama-3.1-8b",
            target_host="small-node-01",
            hardware=HardwareProfile(cpu_cores=4, memory_gb=8, gpu_count=0),
        )

        response = DeploymentPlanner().create_plan(request)

        self.assertEqual(response.plan.risk, "high")
        self.assertGreaterEqual(len(response.plan.warnings), 2)


if __name__ == "__main__":
    unittest.main()
