from app.models.deployment import InferenceEngine, PlannedCommand
from templates import ollama, vllm


class DeploymentTemplateRegistry:
    def build_commands(
        self,
        engine: InferenceEngine,
        model_name: str,
        port: int,
    ) -> list[PlannedCommand]:
        if engine == InferenceEngine.ollama:
            return ollama.build_commands(model_name, port)
        if engine == InferenceEngine.vllm:
            return vllm.build_commands(model_name, port)

        return [
            PlannedCommand(
                command=(
                    "docker run -d "
                    f"--name modelops-{model_name.replace('/', '-').replace(':', '-')} "
                    f"-p {port}:{port} "
                    f"-e MODEL_NAME={model_name} "
                    "ghcr.io/modelops/runtime:latest"
                ),
                description="Run a generic model serving container.",
            )
        ]
