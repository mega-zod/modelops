from app.models.deployment import DeploymentRisk, HardwareProfile, ModelProfile


class HardwareAnalyzer:
    def assess(self, hardware: HardwareProfile, model: ModelProfile) -> tuple[DeploymentRisk, list[str]]:
        warnings: list[str] = []

        if hardware.memory_gb < model.min_memory_gb:
            warnings.append(
                f"Host memory is below the recommended minimum of {model.min_memory_gb:g} GB."
            )

        if model.min_gpu_memory_gb is not None:
            if hardware.gpu_count == 0:
                message = "No GPU was reported for a GPU-recommended model."
                if model.gpu_required:
                    message = "No GPU was reported for a GPU-required model."
                warnings.append(message)
            elif hardware.gpu_memory_gb is not None and hardware.gpu_memory_gb < model.min_gpu_memory_gb:
                warnings.append(
                    f"GPU memory is below the recommended minimum of {model.min_gpu_memory_gb:g} GB."
                )

        if model.gpu_required and hardware.gpu_count == 0:
            warnings.append(f"{model.name} is marked GPU-required in the model catalog.")

        if len(warnings) >= 2:
            return DeploymentRisk.high, warnings
        if warnings:
            return DeploymentRisk.medium, warnings
        return DeploymentRisk.low, warnings
