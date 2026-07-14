import json
from typing import Any

import httpx

from app.models.deployment import (
    DeploymentPlan,
    DeploymentVerificationReport,
    InferenceEngine,
    VerificationCheck,
    VerificationStatus,
)


class DeploymentVerifier:
    def __init__(self, client: httpx.Client | None = None, timeout_seconds: float = 10.0) -> None:
        self.client = client or httpx.Client(timeout=timeout_seconds)

    def build_checks(self, plan: DeploymentPlan) -> list[str]:
        if plan.runtime == InferenceEngine.ollama.value:
            return [
                f"curl -fsS http://{plan.target_host}:{plan.port}/api/tags",
                (
                    "curl -fsS "
                    f"http://{plan.target_host}:{plan.port}/api/generate "
                    "-H 'Content-Type: application/json' "
                    f"-d '{{\"model\":\"{plan.model_name}\",\"prompt\":\"ping\",\"stream\":false}}'"
                ),
            ]

        return [
            f"curl -fsS http://{plan.target_host}:{plan.port}/health",
            f"curl -fsS http://{plan.target_host}:{plan.port}/v1/models",
            (
                "curl -fsS "
                f"http://{plan.target_host}:{plan.port}/v1/completions "
                "-H 'Content-Type: application/json' "
                f"-d '{{\"model\":\"{plan.model_name}\",\"prompt\":\"ping\",\"max_tokens\":1}}'"
            ),
        ]

    def verify(self, plan: DeploymentPlan) -> DeploymentVerificationReport:
        if plan.runtime == InferenceEngine.ollama.value:
            checks = self._verify_ollama(plan)
        else:
            checks = self._verify_openai_compatible(plan)

        return DeploymentVerificationReport(
            model_name=plan.model_name,
            target_host=plan.target_host,
            runtime=plan.runtime,
            port=plan.port,
            success=all(check.status == VerificationStatus.passed for check in checks),
            checks=checks,
        )

    def _verify_ollama(self, plan: DeploymentPlan) -> list[VerificationCheck]:
        base_url = self._base_url(plan)
        tags_url = f"{base_url}/api/tags"
        generate_url = f"{base_url}/api/generate"

        tags_response = self._get(tags_url)
        model_available = self._ollama_model_available(tags_response.get("json"), plan.model_name)
        generate_response = self._post(
            generate_url,
            {"model": plan.model_name, "prompt": "ping", "stream": False},
        )

        return [
            self._check_from_response("service_running", tags_url, tags_response),
            VerificationCheck(
                name="model_available",
                url=tags_url,
                status=VerificationStatus.passed if model_available else VerificationStatus.failed,
                detail="Model is listed by Ollama." if model_available else "Model was not found in Ollama tags.",
            ),
            self._check_from_response("api_responds", generate_url, generate_response),
        ]

    def _verify_openai_compatible(self, plan: DeploymentPlan) -> list[VerificationCheck]:
        base_url = self._base_url(plan)
        health_url = f"{base_url}/health"
        models_url = f"{base_url}/v1/models"
        completions_url = f"{base_url}/v1/completions"

        health_response = self._get(health_url)
        models_response = self._get(models_url)
        model_available = self._openai_model_available(models_response.get("json"), plan.model_name)
        completions_response = self._post(
            completions_url,
            {"model": plan.model_name, "prompt": "ping", "max_tokens": 1},
        )

        return [
            self._check_from_response("service_running", health_url, health_response),
            VerificationCheck(
                name="model_available",
                url=models_url,
                status=VerificationStatus.passed if model_available else VerificationStatus.failed,
                detail="Model is listed by the OpenAI-compatible API."
                if model_available
                else "Model was not found in /v1/models.",
            ),
            self._check_from_response("api_responds", completions_url, completions_response),
        ]

    def _base_url(self, plan: DeploymentPlan) -> str:
        return f"http://{plan.target_host}:{plan.port}"

    def _get(self, url: str) -> dict[str, Any]:
        try:
            response = self.client.get(url)
            return self._response_payload(response)
        except httpx.HTTPError as exc:
            return {"ok": False, "detail": str(exc)}

    def _post(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            response = self.client.post(url, json=payload)
            return self._response_payload(response)
        except httpx.HTTPError as exc:
            return {"ok": False, "detail": str(exc)}

    def _response_payload(self, response: httpx.Response) -> dict[str, Any]:
        body: Any = None
        try:
            body = response.json()
        except (json.JSONDecodeError, ValueError):
            body = response.text

        return {
            "ok": 200 <= response.status_code < 300,
            "status_code": response.status_code,
            "json": body,
            "detail": f"HTTP {response.status_code}",
        }

    def _check_from_response(self, name: str, url: str, payload: dict[str, Any]) -> VerificationCheck:
        return VerificationCheck(
            name=name,
            url=url,
            status=VerificationStatus.passed if payload.get("ok") else VerificationStatus.failed,
            detail=str(payload.get("detail", "Request completed.")),
        )

    def _ollama_model_available(self, payload: Any, model_name: str) -> bool:
        if not isinstance(payload, dict):
            return False
        models = payload.get("models", [])
        return any(item.get("name") == model_name for item in models if isinstance(item, dict))

    def _openai_model_available(self, payload: Any, model_name: str) -> bool:
        if not isinstance(payload, dict):
            return False
        models = payload.get("data", [])
        return any(item.get("id") == model_name for item in models if isinstance(item, dict))
