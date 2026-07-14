import re

from app.models.intent import IntentClassification, IntentType
from app.services.model_catalog import normalize_model_name


class IntentParser:
    _host_pattern = re.compile(r"\b(?:[a-z0-9]+(?:-[a-z0-9]+)+)(?:\.[a-z0-9.-]+)?\b", re.IGNORECASE)
    _memory_pattern = re.compile(r"(?P<value>\d+(?:\.\d+)?)\s*gb\s*(?:ram|memory)\b", re.IGNORECASE)
    _gpu_memory_pattern = re.compile(r"(?P<value>\d+(?:\.\d+)?)\s*gb\s*gpu(?:\s*memory)?\b", re.IGNORECASE)
    _gpu_count_pattern = re.compile(r"(?P<value>\d+)\s*gpus?\b", re.IGNORECASE)
    _cpu_pattern = re.compile(r"(?P<value>\d+)\s*cpu(?:s| cores?)?\b", re.IGNORECASE)

    def parse(self, message: str) -> IntentClassification:
        text = message.strip()
        lowered = text.lower()
        assumptions: list[str] = []
        signals: list[str] = []

        intent = IntentType.general_question
        if any(keyword in lowered for keyword in ("execute", "run it", "go ahead", "approved", "authorize")):
            intent = IntentType.execution_request
            signals.append("execution_keyword")
        elif any(keyword in lowered for keyword in ("deploy", "plan", "launch", "serve", "spin up")):
            intent = IntentType.deployment_request
            signals.append("deployment_keyword")
        elif lowered.endswith("?") or any(keyword in lowered for keyword in ("what", "how", "why")):
            intent = IntentType.general_question
            signals.append("question_keyword")

        model_name = self._find_model_name(lowered)
        if model_name:
            signals.append("model_name")

        target_host = self._find_target_host(text)
        if target_host:
            signals.append("target_host")

        cpu_cores = self._find_int(lowered, self._cpu_pattern)
        if cpu_cores is not None:
            signals.append("cpu_cores")
        else:
            assumptions.append("Assuming 8 CPU cores until the user specifies otherwise.")
            cpu_cores = 8

        memory_gb = self._find_float(lowered, self._memory_pattern)
        if memory_gb is not None:
            signals.append("memory_gb")

        gpu_count = self._find_int(lowered, self._gpu_count_pattern)
        if gpu_count is not None:
            signals.append("gpu_count")

        gpu_memory_gb = self._find_float(lowered, self._gpu_memory_pattern)
        if gpu_memory_gb is not None:
            signals.append("gpu_memory_gb")

        confidence = 0.25
        confidence += 0.2 if model_name else 0.0
        confidence += 0.2 if target_host else 0.0
        confidence += 0.1 if memory_gb is not None else 0.0
        confidence += 0.1 if cpu_cores is not None else 0.0
        confidence += 0.05 if gpu_count is not None else 0.0
        confidence += 0.05 if gpu_memory_gb is not None else 0.0
        confidence += 0.05 if intent == IntentType.execution_request else 0.0

        return IntentClassification(
            intent=intent,
            confidence=min(confidence, 1.0),
            model_name=model_name,
            target_host=target_host,
            cpu_cores=cpu_cores,
            memory_gb=memory_gb,
            gpu_count=gpu_count,
            gpu_memory_gb=gpu_memory_gb,
            assumptions=assumptions,
            signals=signals,
        )

    def _find_model_name(self, lowered: str) -> str | None:
        candidates = [
            "llama3.3:70b",
            "llama3.1:8b",
            "qwen3:32b",
            "qwen3:8b",
            "gemma3:27b",
            "gemma3:12b",
            "deepseek-r1:32b",
            "deepseek-r1:8b",
        ]
        for candidate in candidates:
            normalized = normalize_model_name(candidate)
            if candidate in lowered or normalized in lowered:
                return normalized
            alias = candidate.replace(":", "-")
            if alias in lowered:
                return normalized
        return None

    def _find_target_host(self, text: str) -> str | None:
        match = self._host_pattern.search(text)
        if match:
            candidate = match.group(0)
            if any(token in candidate.lower() for token in ("node", "host", "gpu", "server", "compute")):
                return candidate
        return None

    def _find_int(self, lowered: str, pattern: re.Pattern[str]) -> int | None:
        match = pattern.search(lowered)
        return int(match.group("value")) if match else None

    def _find_float(self, lowered: str, pattern: re.Pattern[str]) -> float | None:
        match = pattern.search(lowered)
        return float(match.group("value")) if match else None
