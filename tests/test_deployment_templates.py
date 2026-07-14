import unittest

from app.models.deployment import InferenceEngine
from app.services.deployment_templates import DeploymentTemplateRegistry


class DeploymentTemplateTests(unittest.TestCase):
    def test_ollama_template_generates_model_pull(self) -> None:
        commands = DeploymentTemplateRegistry().build_commands(InferenceEngine.ollama, "qwen3:8b", 11434)

        command_text = "\n".join(command.command for command in commands)
        self.assertIn("ollama pull qwen3:8b", command_text)
        self.assertIn("OLLAMA_HOST=0.0.0.0:11434", command_text)

    def test_vllm_template_generates_openai_compatible_server(self) -> None:
        commands = DeploymentTemplateRegistry().build_commands(InferenceEngine.vllm, "llama3.3:70b", 8000)

        command_text = "\n".join(command.command for command in commands)
        self.assertIn("vllm.entrypoints.openai.api_server", command_text)
        self.assertIn("--model llama3.3:70b", command_text)
        self.assertIn("--port 8000", command_text)


if __name__ == "__main__":
    unittest.main()
