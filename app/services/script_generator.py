from pathlib import Path

from app.models.deployment import DeploymentScript, PlannedCommand


class DeploymentScriptGenerator:
    def __init__(self, output_dir: Path | str = "generated") -> None:
        self.output_dir = Path(output_dir)

    def generate(
        self,
        *,
        model_name: str,
        engine: str,
        target_host: str,
        port: int,
        commands: list[PlannedCommand],
        verification_steps: list[str],
    ) -> DeploymentScript:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        script_path = self.output_dir / "deploy.sh"
        content = self._render_bash(
            model_name=model_name,
            engine=engine,
            target_host=target_host,
            port=port,
            commands=commands,
            verification_steps=verification_steps,
        )
        script_path.write_text(content, encoding="utf-8")
        return DeploymentScript(path=str(script_path), content=content)

    def _render_bash(
        self,
        *,
        model_name: str,
        engine: str,
        target_host: str,
        port: int,
        commands: list[PlannedCommand],
        verification_steps: list[str],
    ) -> str:
        lines = [
            "#!/usr/bin/env bash",
            "set -euo pipefail",
            "",
            f"# ModelOps AI deployment script for {model_name}",
            f"# Engine: {engine}",
            f"# Target host: {target_host}",
            "",
        ]

        for index, planned_command in enumerate(commands, start=1):
            lines.extend(
                [
                    f"echo '[{index}/{len(commands)}] {planned_command.description}'",
                    planned_command.command,
                    "",
                ]
            )

        lines.append("echo 'Deployment commands completed. Suggested verification:'")
        for step in verification_steps:
            lines.append(f"echo '- {step}'")
        lines.extend(
            [
                "",
                "echo 'Running basic HTTP verification...'",
                "python3 - <<'PY'",
                "import sys",
                "import urllib.request",
                "",
                f"base_url = 'http://{target_host}:{port}'",
                "for path in ('/health', '/v1/models', '/api/tags'):",
                "    url = base_url + path",
                "    try:",
                "        with urllib.request.urlopen(url, timeout=10) as response:",
                "            if 200 <= response.status < 300:",
                "                print(f'OK {url}')",
                "                sys.exit(0)",
                "    except Exception as exc:",
                "        print(f'SKIP {url}: {exc}')",
                "print('No known health endpoint responded successfully.')",
                "sys.exit(1)",
                "PY",
            ]
        )
        lines.append("")

        return "\n".join(lines)
