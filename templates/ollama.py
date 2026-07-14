from app.models.deployment import PlannedCommand
from templates.common import command, sanitize_name


def build_commands(model_name: str, port: int) -> list[PlannedCommand]:
    service_name = f"modelops-{sanitize_name(model_name)}"
    return [
        command(
            "if ! command -v curl >/dev/null 2>&1; then sudo apt-get update && sudo apt-get install -y curl; fi",
            "Ensure curl is available for the Ollama installer.",
        ),
        command(
            "curl -fsSL https://ollama.com/install.sh | sh",
            "Install Ollama on the Ubuntu host.",
        ),
        command(
            "sudo systemctl enable --now ollama",
            "Start Ollama as a system service.",
        ),
        command(
            f"ollama pull {model_name}",
            "Download the requested model into Ollama.",
        ),
        command(
            (
                f"sudo systemctl set-environment OLLAMA_HOST=0.0.0.0:{port} "
                f"&& sudo systemctl restart ollama"
            ),
            f"Expose Ollama on port {port}.",
        ),
        command(
            f"printf '%s\\n' '{service_name} ready on Ollama port {port}'",
            "Print a deployment summary.",
        ),
    ]
