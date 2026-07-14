from app.models.deployment import EngineRecommendation, HardwareProfile, InferenceEngine, ModelProfile


MODEL_CATALOG: dict[str, ModelProfile] = {
    "qwen3:8b": ModelProfile(
        name="qwen3:8b",
        family="qwen",
        parameter_size_b=8,
        min_memory_gb=16,
        gpu_required=False,
        supports_cpu=True,
        recommended_runtime=InferenceEngine.ollama,
        default_port=11434,
    ),
    "qwen3:32b": ModelProfile(
        name="qwen3:32b",
        family="qwen",
        parameter_size_b=32,
        min_memory_gb=48,
        min_gpu_memory_gb=24,
        gpu_required=False,
        supports_cpu=True,
        recommended_runtime=InferenceEngine.vllm,
        default_port=8000,
    ),
    "llama3.1:8b": ModelProfile(
        name="llama3.1:8b",
        family="llama",
        parameter_size_b=8,
        min_memory_gb=16,
        min_gpu_memory_gb=16,
        gpu_required=False,
        supports_cpu=True,
        recommended_runtime=InferenceEngine.ollama,
        default_port=11434,
    ),
    "llama3.3:70b": ModelProfile(
        name="llama3.3:70b",
        family="llama",
        parameter_size_b=70,
        min_memory_gb=96,
        min_gpu_memory_gb=48,
        gpu_required=True,
        supports_cpu=False,
        recommended_runtime=InferenceEngine.vllm,
        default_port=8000,
    ),
    "gemma3:12b": ModelProfile(
        name="gemma3:12b",
        family="gemma",
        parameter_size_b=12,
        min_memory_gb=24,
        gpu_required=False,
        supports_cpu=True,
        recommended_runtime=InferenceEngine.ollama,
        default_port=11434,
    ),
    "gemma3:27b": ModelProfile(
        name="gemma3:27b",
        family="gemma",
        parameter_size_b=27,
        min_memory_gb=48,
        min_gpu_memory_gb=24,
        gpu_required=False,
        supports_cpu=True,
        recommended_runtime=InferenceEngine.vllm,
        default_port=8000,
    ),
    "deepseek-r1:8b": ModelProfile(
        name="deepseek-r1:8b",
        family="deepseek",
        parameter_size_b=8,
        min_memory_gb=16,
        gpu_required=False,
        supports_cpu=True,
        recommended_runtime=InferenceEngine.ollama,
        default_port=11434,
    ),
    "deepseek-r1:32b": ModelProfile(
        name="deepseek-r1:32b",
        family="deepseek",
        parameter_size_b=32,
        min_memory_gb=64,
        min_gpu_memory_gb=24,
        gpu_required=False,
        supports_cpu=True,
        recommended_runtime=InferenceEngine.vllm,
        default_port=8000,
    ),
}

ALIASES = {
    "qwen3-8b": "qwen3:8b",
    "qwen3-32b": "qwen3:32b",
    "llama-3.1-8b": "llama3.1:8b",
    "llama3.1-8b": "llama3.1:8b",
    "llama-3.3-70b": "llama3.3:70b",
    "llama3.3-70b": "llama3.3:70b",
    "gemma3-12b": "gemma3:12b",
    "gemma3-27b": "gemma3:27b",
    "deepseek-r1-8b": "deepseek-r1:8b",
    "deepseek-r1-32b": "deepseek-r1:32b",
}


def normalize_model_name(model_name: str) -> str:
    normalized = model_name.strip().lower()
    return ALIASES.get(normalized, normalized)


def get_model_profile(model_name: str) -> ModelProfile | None:
    return MODEL_CATALOG.get(normalize_model_name(model_name))


def list_models() -> list[ModelProfile]:
    return list(MODEL_CATALOG.values())


def recommend_inference_engine(
    model: ModelProfile,
    hardware: HardwareProfile,
) -> EngineRecommendation:
    warnings: list[str] = []
    has_gpu = hardware.gpu_count > 0
    has_enough_gpu_memory = (
        model.min_gpu_memory_gb is not None
        and hardware.gpu_memory_gb is not None
        and hardware.gpu_memory_gb >= model.min_gpu_memory_gb
    )

    if model.gpu_required:
        if has_gpu and has_enough_gpu_memory:
            return EngineRecommendation(
                engine=InferenceEngine.vllm,
                reason=(
                    f"{model.name} requires GPU acceleration and this host reports "
                    f"{hardware.gpu_memory_gb:g} GB GPU memory."
                ),
            )
        warnings.append(f"{model.name} requires a GPU with at least {model.min_gpu_memory_gb:g} GB memory.")
        return EngineRecommendation(
            engine=InferenceEngine.vllm,
            reason="vLLM is selected because the model is GPU-only, but hardware is insufficient.",
            warnings=warnings,
        )

    if has_gpu and model.min_gpu_memory_gb is not None and has_enough_gpu_memory:
        return EngineRecommendation(
            engine=InferenceEngine.vllm,
            reason=(
                f"GPU deployment is available with {hardware.gpu_memory_gb:g} GB GPU memory, "
                "so vLLM should provide better throughput."
            ),
        )

    if model.supports_cpu and hardware.memory_gb >= model.min_memory_gb:
        return EngineRecommendation(
            engine=InferenceEngine.ollama,
            reason=f"CPU deployment is viable with {hardware.memory_gb:g} GB RAM.",
        )

    if not model.supports_cpu:
        warnings.append(f"{model.name} does not support the CPU-only MVP path.")
    if hardware.memory_gb < model.min_memory_gb:
        warnings.append(f"Host RAM is below the recommended {model.min_memory_gb:g} GB.")

    return EngineRecommendation(
        engine=model.recommended_runtime,
        reason="Selected the catalog default engine because no ideal hardware match was found.",
        warnings=warnings,
    )
