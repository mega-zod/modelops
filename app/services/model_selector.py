from app.models.deployment import HardwareProfile, InferenceEngine, ModelProfile
from app.services.model_catalog import get_model_profile, recommend_inference_engine


class ModelSelector:
    def select(self, model_name: str) -> ModelProfile:
        profile = get_model_profile(model_name)
        if profile is not None:
            return profile

        return ModelProfile(
            name=model_name,
            family="custom",
            min_memory_gb=16,
            recommended_runtime=InferenceEngine.docker,
            default_port=8000,
        )

    def recommend_runtime(self, model: ModelProfile, hardware: HardwareProfile) -> str:
        return recommend_inference_engine(model, hardware).engine.value
