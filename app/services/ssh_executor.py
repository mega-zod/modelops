from dataclasses import dataclass

import paramiko

from app.models.deployment import CommandExecutionResult, PlannedCommand


@dataclass(frozen=True)
class SSHConnectionConfig:
    host: str
    username: str
    port: int = 22
    password: str | None = None
    key_filename: str | None = None
    timeout_seconds: int = 15


class SSHExecutor:
    def execute(
        self,
        *,
        connection: SSHConnectionConfig,
        commands: list[PlannedCommand],
        authorized: bool,
    ) -> list[CommandExecutionResult]:
        if not authorized:
            raise PermissionError("Remote command execution requires explicit authorization.")

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            client.connect(
                hostname=connection.host,
                port=connection.port,
                username=connection.username,
                password=connection.password,
                key_filename=connection.key_filename,
                timeout=connection.timeout_seconds,
                banner_timeout=connection.timeout_seconds,
                auth_timeout=connection.timeout_seconds,
            )

            results: list[CommandExecutionResult] = []
            for planned_command in commands:
                stdin, stdout, stderr = client.exec_command(planned_command.command)
                exit_code = stdout.channel.recv_exit_status()
                results.append(
                    CommandExecutionResult(
                        command=planned_command.command,
                        exit_code=exit_code,
                        stdout=stdout.read().decode("utf-8", errors="replace"),
                        stderr=stderr.read().decode("utf-8", errors="replace"),
                    )
                )

            return results
        finally:
            client.close()
