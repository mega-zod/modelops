import unittest

import httpx

from app.models.deployment import DeploymentPlan, DeploymentRisk
from app.services.verifier import DeploymentVerifier


class DeploymentVerifierTests(unittest.TestCase):
    def test_verify_vllm_success(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/health":
                return httpx.Response(200, json={"status": "ok"})
            if request.url.path == "/v1/models":
                return httpx.Response(200, json={"data": [{"id": "llama3.3:70b"}]})
            if request.url.path == "/v1/completions":
                return httpx.Response(200, json={"choices": [{"text": "pong"}]})
            return httpx.Response(404)

        report = DeploymentVerifier(
            client=httpx.Client(transport=httpx.MockTransport(handler))
        ).verify(self._plan(runtime="vllm", model_name="llama3.3:70b", port=8000))

        self.assertTrue(report.success)
        self.assertEqual([check.status for check in report.checks], ["passed", "passed", "passed"])

    def test_verify_ollama_fails_when_model_missing(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/api/tags":
                return httpx.Response(200, json={"models": [{"name": "qwen3:8b"}]})
            if request.url.path == "/api/generate":
                return httpx.Response(200, json={"response": "pong"})
            return httpx.Response(404)

        report = DeploymentVerifier(
            client=httpx.Client(transport=httpx.MockTransport(handler))
        ).verify(self._plan(runtime="ollama", model_name="deepseek-r1:8b", port=11434))

        self.assertFalse(report.success)
        self.assertEqual(report.checks[1].name, "model_available")
        self.assertEqual(report.checks[1].status, "failed")

    def _plan(self, runtime: str, model_name: str, port: int) -> DeploymentPlan:
        return DeploymentPlan(
            model_name=model_name,
            target_host="127.0.0.1",
            runtime=runtime,
            port=port,
            risk=DeploymentRisk.low,
            reason="test",
            summary="test",
            commands=[],
            verification_steps=[],
        )


if __name__ == "__main__":
    unittest.main()
