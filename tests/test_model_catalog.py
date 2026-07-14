import unittest

from app.models.deployment import HardwareProfile, InferenceEngine
from app.services.model_catalog import get_model_profile, list_models, recommend_inference_engine


class ModelCatalogTests(unittest.TestCase):
    def test_catalog_contains_mvp_families(self) -> None:
        families = {model.family for model in list_models()}

        self.assertIn("qwen", families)
        self.assertIn("llama", families)
        self.assertIn("gemma", families)
        self.assertIn("deepseek", families)

    def test_alias_lookup_resolves_llama_name(self) -> None:
        model = get_model_profile("llama-3.3-70b")

        self.assertIsNotNone(model)
        self.assertEqual(model.name, "llama3.3:70b")
        self.assertTrue(model.gpu_required)

    def test_cpu_viable_model_recommends_ollama(self) -> None:
        model = get_model_profile("qwen3:8b")
        self.assertIsNotNone(model)

        recommendation = recommend_inference_engine(
            model,
            HardwareProfile(cpu_cores=8, memory_gb=32, gpu_count=0),
        )

        self.assertEqual(recommendation.engine, InferenceEngine.ollama)
        self.assertIn("CPU deployment", recommendation.reason)

    def test_large_gpu_model_recommends_vllm(self) -> None:
        model = get_model_profile("llama3.3:70b")
        self.assertIsNotNone(model)

        recommendation = recommend_inference_engine(
            model,
            HardwareProfile(cpu_cores=32, memory_gb=128, gpu_count=1, gpu_memory_gb=80),
        )

        self.assertEqual(recommendation.engine, InferenceEngine.vllm)
        self.assertEqual(recommendation.warnings, [])


if __name__ == "__main__":
    unittest.main()
