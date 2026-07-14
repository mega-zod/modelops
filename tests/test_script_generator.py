import tempfile
import unittest
from pathlib import Path

from app.models.deployment import PlannedCommand
from app.services.script_generator import DeploymentScriptGenerator


class DeploymentScriptGeneratorTests(unittest.TestCase):
    def test_generate_writes_reviewable_bash_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = DeploymentScriptGenerator(output_dir=Path(tmpdir))

            script = generator.generate(
                model_name="qwen3:8b",
                engine="ollama",
                target_host="gpu-node-01",
                port=11434,
                commands=[
                    PlannedCommand(command="ollama pull qwen3:8b", description="Pull model"),
                ],
                verification_steps=["Call health endpoint"],
            )

            path = Path(script.path)
            self.assertTrue(path.exists())
            self.assertIn("#!/usr/bin/env bash", script.content)
            self.assertIn("ollama pull qwen3:8b", path.read_text(encoding="utf-8"))
            self.assertIn("Call health endpoint", script.content)


if __name__ == "__main__":
    unittest.main()
