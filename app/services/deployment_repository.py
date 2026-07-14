import sqlite3
from pathlib import Path
from contextlib import contextmanager
from uuid import uuid4

from app.core.config import get_settings
from app.models.deployment import (
    DeploymentExecutionEntry,
    DeploymentExecutionReport,
    DeploymentPlan,
    DeploymentRecord,
    DeploymentSummary,
    ExecutionHistoryItem,
    ExecutionStatus,
)


class DeploymentRepository:
    def __init__(self, db_path: str | Path | None = None) -> None:
        settings = get_settings()
        self.db_path = Path(db_path or settings.database_path)

    def initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS deployments (
                    deployment_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    plan_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS executions (
                    execution_id TEXT PRIMARY KEY,
                    deployment_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    report_json TEXT NOT NULL,
                    FOREIGN KEY(deployment_id) REFERENCES deployments(deployment_id)
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_executions_deployment_id ON executions(deployment_id)"
            )

    def save_plan(self, plan: DeploymentPlan) -> DeploymentRecord:
        self.initialize()
        deployment_id = plan.deployment_id or uuid4().hex
        stored_plan = plan.model_copy(update={"deployment_id": deployment_id})
        now = self._now()

        with self._connect() as conn:
            row = conn.execute(
                "SELECT created_at FROM deployments WHERE deployment_id = ?",
                (deployment_id,),
            ).fetchone()
            created_at = row["created_at"] if row else now
            if row:
                conn.execute(
                    """
                    UPDATE deployments
                    SET updated_at = ?, plan_json = ?
                    WHERE deployment_id = ?
                    """,
                    (now, stored_plan.model_dump_json(), deployment_id),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO deployments (deployment_id, created_at, updated_at, plan_json)
                    VALUES (?, ?, ?, ?)
                    """,
                    (deployment_id, created_at, now, stored_plan.model_dump_json()),
                )

        return self.get_record(deployment_id) or DeploymentRecord(
            deployment_id=deployment_id,
            created_at=created_at,
            updated_at=now,
            plan=stored_plan,
            executions=[],
        )

    def save_execution(self, deployment_id: str, report: DeploymentExecutionReport) -> DeploymentExecutionEntry:
        self.initialize()
        execution_id = report.execution_id or uuid4().hex
        created_at = self._now()
        stored_report = report.model_copy(
            update={
                "deployment_id": deployment_id,
                "execution_id": execution_id,
                "plan": report.plan.model_copy(update={"deployment_id": deployment_id}),
            }
        )

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO executions (execution_id, deployment_id, created_at, report_json)
                VALUES (?, ?, ?, ?)
                """,
                (execution_id, deployment_id, created_at, stored_report.model_dump_json()),
            )
            conn.execute(
                "UPDATE deployments SET updated_at = ? WHERE deployment_id = ?",
                (created_at, deployment_id),
            )

        return DeploymentExecutionEntry(execution_id=execution_id, created_at=created_at, report=stored_report)

    def get_record(self, deployment_id: str) -> DeploymentRecord | None:
        self.initialize()
        with self._connect() as conn:
            deployment_row = conn.execute(
                "SELECT deployment_id, created_at, updated_at, plan_json FROM deployments WHERE deployment_id = ?",
                (deployment_id,),
            ).fetchone()
            if deployment_row is None:
                return None

            plan = DeploymentPlan.model_validate_json(deployment_row["plan_json"])
            execution_rows = conn.execute(
                """
                SELECT execution_id, created_at, report_json
                FROM executions
                WHERE deployment_id = ?
                ORDER BY created_at ASC
                """,
                (deployment_id,),
            ).fetchall()
            executions = [
                DeploymentExecutionEntry(
                    execution_id=row["execution_id"],
                    created_at=row["created_at"],
                    report=DeploymentExecutionReport.model_validate_json(row["report_json"]),
                )
                for row in execution_rows
            ]
            execution_history = [
                self._execution_history_item(entry)
                for entry in executions
            ]

            return DeploymentRecord(
                deployment_id=deployment_row["deployment_id"],
                created_at=deployment_row["created_at"],
                updated_at=deployment_row["updated_at"],
                plan=plan,
                executions=executions,
                execution_history=execution_history,
                status_line=self._status_line(plan, execution_history),
            )

    def list_deployments(self, limit: int = 50) -> list[DeploymentSummary]:
        self.initialize()
        with self._connect() as conn:
            deployment_rows = conn.execute(
                """
                SELECT deployment_id, created_at, updated_at, plan_json
                FROM deployments
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            execution_rows = conn.execute(
                """
                SELECT deployment_id, created_at, report_json
                FROM executions
                ORDER BY created_at ASC
                """
            ).fetchall()

        execution_counts: dict[str, int] = {}
        last_status: dict[str, ExecutionStatus | None] = {}
        last_executed_at: dict[str, str | None] = {}
        last_message: dict[str, str | None] = {}
        for row in execution_rows:
            deployment_id = row["deployment_id"]
            execution_counts[deployment_id] = execution_counts.get(deployment_id, 0) + 1
            report = DeploymentExecutionReport.model_validate_json(row["report_json"])
            last_status[deployment_id] = report.execution_status
            last_executed_at[deployment_id] = row["created_at"]
            last_message[deployment_id] = report.message

        summaries: list[DeploymentSummary] = []
        for row in deployment_rows:
            plan = DeploymentPlan.model_validate_json(row["plan_json"])
            summaries.append(
                DeploymentSummary(
                    deployment_id=row["deployment_id"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    model_name=plan.model_name,
                    target_host=plan.target_host,
                    runtime=plan.runtime,
                    port=plan.port,
                    execution_count=execution_counts.get(row["deployment_id"], 0),
                    last_executed_at=last_executed_at.get(row["deployment_id"]),
                    last_execution_status=last_status.get(row["deployment_id"]),
                    last_execution_message=last_message.get(row["deployment_id"]),
                    status_line=self._summary_status_line(
                        plan.model_name,
                        plan.target_host,
                        execution_counts.get(row["deployment_id"], 0),
                        last_status.get(row["deployment_id"]),
                        last_executed_at.get(row["deployment_id"]),
                    ),
                )
            )
        return summaries

    def get_execution_history(self, deployment_id: str) -> list[ExecutionHistoryItem]:
        record = self.get_record(deployment_id)
        return record.execution_history if record is not None else []

    def get_latest_record(self) -> DeploymentRecord | None:
        self.initialize()
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT deployment_id
                FROM deployments
                ORDER BY updated_at DESC
                LIMIT 1
                """
            ).fetchone()

        if row is None:
            return None
        return self.get_record(row["deployment_id"])

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def _now(self) -> str:
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()

    def _execution_history_item(self, entry: DeploymentExecutionEntry) -> ExecutionHistoryItem:
        report = entry.report
        command_preview = [result.command for result in report.command_results[:2]]
        verification_success = None
        if report.verification_report is not None:
            verification_success = report.verification_report.success

        return ExecutionHistoryItem(
            execution_id=entry.execution_id,
            created_at=entry.created_at,
            execution_status=report.execution_status,
            runtime=report.plan.runtime,
            port=report.plan.port,
            command_count=len(report.command_results),
            command_preview=command_preview,
            verification_success=verification_success,
            message=report.message,
            status_line=self._history_status_line(report.plan.model_name, report.plan.target_host, report),
        )

    def _summary_status_line(
        self,
        model_name: str,
        target_host: str,
        execution_count: int,
        last_status: ExecutionStatus | None,
        last_executed_at: str | None,
    ) -> str:
        if execution_count == 0:
            return f"{model_name} on {target_host}: no executions yet."
        status = last_status.value if last_status is not None else "unknown"
        when = last_executed_at or "unknown time"
        return f"{model_name} on {target_host}: {execution_count} execution(s), last {status} at {when}."

    def _status_line(self, plan: DeploymentPlan, execution_history: list[ExecutionHistoryItem]) -> str:
        if not execution_history:
            return f"{plan.model_name} on {plan.target_host}: plan saved, no executions yet."
        latest = execution_history[-1]
        when = latest.created_at
        status = latest.execution_status.value
        return (
            f"{plan.model_name} on {plan.target_host}: last run {status} at {when} "
            f"with {latest.command_count} command(s)."
        )

    def _history_status_line(
        self,
        model_name: str,
        target_host: str,
        report: DeploymentExecutionReport,
    ) -> str:
        verification_suffix = ""
        if report.verification_report is not None:
            verification_suffix = (
                " verified successfully"
                if report.verification_report.success
                else " with verification failures"
            )
        return (
            f"{model_name} on {target_host}: last run {report.execution_status.value}{verification_suffix}."
        )
