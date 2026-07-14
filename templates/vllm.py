from app.models.deployment import PlannedCommand
from templates.common import command, sanitize_name


def build_commands(model_name: str, port: int) -> list[PlannedCommand]:
    service_name = f"modelops-{sanitize_name(model_name)}"
    venv_path = f"$HOME/{service_name}-venv"
    log_path = f"$HOME/{service_name}.log"
    return [
        command(
            "sudo apt-get update && sudo apt-get install -y python3-venv python3-pip",
            "Install Python packaging prerequisites for vLLM.",
        ),
        command(
            f"python3 -m venv {venv_path}",
            "Create an isolated Python environment for vLLM.",
        ),
        command(
            f"{venv_path}/bin/pip install --upgrade pip vllm",
            "Install vLLM into the isolated environment.",
        ),
        command(
            (
                f"nohup {venv_path}/bin/python -m vllm.entrypoints.openai.api_server "
                f"--model {model_name} --host 0.0.0.0 --port {port} "
                f"> {log_path} 2>&1 &"
            ),
            "Start the OpenAI-compatible vLLM server.",
        ),
        command(
            f"printf '%s\\n' '{service_name} ready on vLLM port {port}; logs at {log_path}'",
            "Print a deployment summary.",
        ),
    ]
