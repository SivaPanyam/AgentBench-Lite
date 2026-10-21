
"""Run reproducible baseline-versus-recovery benchmark experiments."""

from collections import defaultdict
from dataclasses import fields, is_dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from agentbench.agent import AgentConfig, AgentResult, MockModel, run_agent
from agentbench.benchmark import BenchmarkTask, validate_benchmark
from agentbench.execution import create_default_registry


STRATEGIES = ("baseline", "recovery")


def _to_jsonable(value: Any) -> Any:
    """Convert supported Python values into JSON-compatible data."""
    if is_dataclass(value) and not isinstance(value, type):
        return {
            item.name: _to_jsonable(getattr(value, item.name))
            for item in fields(value)
        }

    if isinstance(value, dict):
        return {str(key): _to_jsonable(item) for key, item in value.items()}

    if isinstance(value, (list, tuple)):
        return [_to_jsonable(item) for item in value]

    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    return repr(value)


def _expected_status_for_strategy(
    task: BenchmarkTask,
    strategy: str,
) -> str:
    """Return the expected terminal status for a strategy and task."""
    if task.category == "recovery_success":
        return "success" if strategy == "recovery" else "failed"

    return task.expected_status


def _run_one_task(
    task: BenchmarkTask,
    strategy: str,
) -> dict[str, Any]:
    """Run one task with an independent model and tool registry."""
    model = MockModel(list(task.actions))
    registry = create_default_registry()

    config = AgentConfig(
        strategy=strategy,
        max_steps=task.max_steps,
        max_retries=task.max_retries,
    )

    result: AgentResult = run_agent(
        task=task.description,
        expected_result=task.expected_result,
        model=model,
        registry=registry,
        config=config,
    )

    expected_status = _expected_status_for_strategy(task, strategy)

    return {
        "task_id": task.task_id,
        "description": task.description,
        "category": task.category,
        "strategy": strategy,
        "expected_status": expected_status,
        "actual_status": result.status,
        "expected_status_match": result.status == expected_status,
        "expected_result": _to_jsonable(task.expected_result),
        "actual_result": _to_jsonable(result.result),
        "task_success": result.task_success,
        "steps": result.steps,
        "retries_used": result.retries_used,
        "history": _to_jsonable(result.history),
    }


def _build_summary(
    records: list[dict[str, Any]],
    task_count: int,
) -> dict[str, Any]:
    """Calculate overall and per-category benchmark metrics."""
    strategy_summaries: dict[str, Any] = {}

    for strategy in STRATEGIES:
        strategy_records = [
            record
            for record in records
            if record["strategy"] == strategy
        ]

        completed = sum(
            record["task_success"] for record in strategy_records
        )
        run_count = len(strategy_records)
        total_steps = sum(record["steps"] for record in strategy_records)
        total_retries = sum(
            record["retries_used"] for record in strategy_records
        )

        status_counts: dict[str, int] = defaultdict(int)
        category_records: dict[str, list[dict[str, Any]]] = defaultdict(list)

        for record in strategy_records:
            status_counts[record["actual_status"]] += 1
            category_records[record["category"]].append(record)

        by_category: dict[str, Any] = {}

        for category, items in sorted(category_records.items()):
            category_count = len(items)
            category_completed = sum(
                item["task_success"] for item in items
            )

            by_category[category] = {
                "task_count": category_count,
                "completed_tasks": category_completed,
                "failed_tasks": category_count - category_completed,
                "completion_rate": (
                    category_completed / category_count
                    if category_count else 0.0
                ),
                "total_steps": sum(item["steps"] for item in items),
                "total_retries": sum(
                    item["retries_used"] for item in items
                ),
                "status_counts": dict(
                    sorted(
                        (
                            status,
                            sum(
                                item["actual_status"] == status
                                for item in items
                            ),
                        )
                        for status in {
                            item["actual_status"] for item in items
                        }
                    )
                ),
            }

        strategy_summaries[strategy] = {
            "task_count": run_count,
            "completed_tasks": completed,
            "failed_tasks": run_count - completed,
            "completion_rate": completed / run_count if run_count else 0.0,
            "status_match_count": sum(
                record["expected_status_match"]
                for record in strategy_records
            ),
            "status_mismatch_count": sum(
                not record["expected_status_match"]
                for record in strategy_records
            ),
            "total_steps": total_steps,
            "average_steps_per_task": (
                total_steps / run_count if run_count else 0.0
            ),
            "total_retries": total_retries,
            "average_retries_per_task": (
                total_retries / run_count if run_count else 0.0
            ),
            "status_counts": dict(sorted(status_counts.items())),
            "by_category": by_category,
        }

    baseline = strategy_summaries["baseline"]
    recovery = strategy_summaries["recovery"]

    completion_difference = (
        recovery["completion_rate"] - baseline["completion_rate"]
    )

    return {
        "task_count": task_count,
        "strategy_count": len(STRATEGIES),
        "runs_per_strategy": {
            strategy: sum(
                record["strategy"] == strategy for record in records
            )
            for strategy in STRATEGIES
        },
        "strategies": strategy_summaries,
        "comparison": {
            "completion_rate_difference": completion_difference,
            "completion_rate_difference_percentage_points": round(
                completion_difference * 100,
                2,
            ),
            "additional_steps": (
                recovery["total_steps"] - baseline["total_steps"]
            ),
            "additional_retries": (
                recovery["total_retries"] - baseline["total_retries"]
            ),
            "status_mismatches": sum(
                not record["expected_status_match"]
                for record in records
            ),
        },
    }


def run_benchmark(
    tasks: tuple[BenchmarkTask, ...],
    output_dir: str | Path = "results",
    run_id: str | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Run each task under baseline and recovery and save JSON reports.

    A supplied run_id makes filenames predictable. Existing output files
    are protected unless overwrite=True is explicitly supplied.
    """
    validate_benchmark(tasks)

    if run_id is None:
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    allowed_characters = (
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789_-"
    )
    if (
        not isinstance(run_id, str)
        or not run_id.strip()
        or any(character not in allowed_characters for character in run_id)
    ):
        raise ValueError(
            "run_id must contain only letters, numbers, underscores, or hyphens."
        )

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    results_file = output_path / f"benchmark_results_{run_id}.json"
    summary_file = output_path / f"benchmark_summary_{run_id}.json"

    existing_files = [
        path for path in (results_file, summary_file) if path.exists()
    ]

    if existing_files and not overwrite:
        names = ", ".join(str(path) for path in existing_files)
        raise FileExistsError(
            f"Benchmark output already exists: {names}. "
            "Choose a new run_id or set overwrite=True."
        )

    records: list[dict[str, Any]] = []

    for task in tasks:
        for strategy in STRATEGIES:
            records.append(_run_one_task(task, strategy))

    summary = _build_summary(records, len(tasks))
    timestamp = datetime.now(timezone.utc).isoformat()

    results_payload = {
        "experiment": "AgentBench Lite",
        "run_id": run_id,
        "created_at_utc": timestamp,
        "strategies": list(STRATEGIES),
        "methodology": {
            "execution_mode": "deterministic scripted actions",
            "task_order": "benchmark dataset order",
            "model": "MockModel",
            "same_actions_for_both_strategies": True,
            "max_steps_and_retries": "defined per benchmark task",
            "completion_definition": (
                "The agent returned success with a result matching "
                "the expected result."
            ),
            "expected_status_policy": (
                "Recovery-success tasks expect baseline to fail and "
                "recovery to succeed. Other tasks use their declared "
                "expected_status."
            ),
        },
        "results": records,
    }

    summary_payload = {
        "experiment": "AgentBench Lite",
        "run_id": run_id,
        "created_at_utc": timestamp,
        "metrics_definitions": {
            "completion_rate": (
                "Completed tasks divided by total tasks for a strategy."
            ),
            "status_match_count": (
                "Runs whose actual terminal status matched the strategy-"
                "specific expected status."
            ),
            "total_steps": (
                "Total model decisions across all tasks, including retries."
            ),
            "total_retries": (
                "Total corrective retry decisions across all tasks."
            ),
            "completion_rate_difference_percentage_points": (
                "Recovery completion rate minus baseline completion rate, "
                "expressed in percentage points."
            ),
            "additional_steps": (
                "Recovery total steps minus baseline total steps."
            ),
            "additional_retries": (
                "Recovery total retries minus baseline total retries."
            ),
        },
        "summary": summary,
    }

    results_json = json.dumps(
        _to_jsonable(results_payload),
        indent=2,
        sort_keys=True,
        allow_nan=False,
    )
    summary_json = json.dumps(
        _to_jsonable(summary_payload),
        indent=2,
        sort_keys=True,
        allow_nan=False,
    )

    # Both payloads are serialized before output is written.
    results_file.write_text(results_json + "\n", encoding="utf-8")
    summary_file.write_text(summary_json + "\n", encoding="utf-8")

    return {
        "run_id": run_id,
        "task_count": len(tasks),
        "results_file": str(results_file),
        "summary_file": str(summary_file),
        "results": records,
        "summary": summary,
    }


if __name__ == "__main__":
    from benchmarks.tasks import BENCHMARK_TASKS

    report = run_benchmark(BENCHMARK_TASKS)

    print(f"Run ID: {report['run_id']}")
    print(f"Tasks: {report['task_count']}")
    print(f"Detailed results: {report['results_file']}")
    print(f"Summary: {report['summary_file']}")

    for strategy, metrics in report["summary"]["strategies"].items():
        print(
            f"{strategy}: "
            f"{metrics['completed_tasks']}/{metrics['task_count']} completed, "
            f"{metrics['completion_rate']:.1%} completion rate, "
            f"{metrics['total_steps']} steps, "
            f"{metrics['total_retries']} retries, "
            f"{metrics['status_mismatch_count']} status mismatches"
        )

    comparison = report["summary"]["comparison"]
    print(
        "Recovery completion-rate difference: "
        f"{comparison['completion_rate_difference_percentage_points']:+.2f} "
        "percentage points"
    )
