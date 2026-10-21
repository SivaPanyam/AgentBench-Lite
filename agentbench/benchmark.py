
"""Benchmark task definitions and validation for AgentBench Lite."""

from dataclasses import dataclass, field
from typing import Any

from agentbench.agent import AgentAction, AgentConfig


VALID_CATEGORIES = {
    "tool_selection",
    "calculator",
    "unit_conversion",
    "mock_lookup",
    "unknown_tool",
    "validation_failure",
    "execution_failure",
    "malformed_action",
    "model_failure",
    "recovery_success",
    "recovery_failure",
    "step_limit",
    "retry_exhaustion",
}


@dataclass(frozen=True)
class BenchmarkTask:
    """Define one deterministic benchmark task."""

    task_id: str
    description: str
    category: str
    actions: tuple[object, ...]
    expected_result: Any
    expected_status: str
    tags: tuple[str, ...] = field(default_factory=tuple)
    max_steps: int = 5
    max_retries: int = 1

    def __post_init__(self) -> None:
        """Reject invalid task definitions."""

        if not isinstance(self.task_id, str) or not self.task_id.strip():
            raise ValueError("task_id must be a non-empty string.")

        if not isinstance(self.description, str) or not self.description.strip():
            raise ValueError("description must be a non-empty string.")

        if self.category not in VALID_CATEGORIES:
            raise ValueError(f"Unsupported benchmark category: {self.category!r}")

        if not isinstance(self.actions, tuple) or not self.actions:
            raise ValueError("actions must be a non-empty tuple.")

        if not isinstance(self.expected_status, str) or self.expected_status not in {
            "success",
            "failed",
            "invalid_action",
            "model_error",
            "step_limit",
        }:
            raise ValueError("Invalid expected_status.")

        if (
            isinstance(self.max_steps, bool)
            or not isinstance(self.max_steps, int)
            or self.max_steps < 1
        ):
            raise ValueError("max_steps must be a positive integer.")

        if (
            isinstance(self.max_retries, bool)
            or not isinstance(self.max_retries, int)
            or self.max_retries not in (0, 1)
        ):
            raise ValueError("max_retries must be 0 or 1.")

        if not isinstance(self.tags, tuple) or not all(
            isinstance(tag, str) and tag.strip() for tag in self.tags
        ):
            raise ValueError("tags must be a tuple of non-empty strings.")

        for action in self.actions:
            if isinstance(action, AgentAction):
                if not isinstance(action.tool_name, str) or not action.tool_name.strip():
                    raise ValueError("AgentAction tool_name must be non-empty.")

                if not isinstance(action.arguments, dict):
                    raise ValueError("AgentAction arguments must be a dictionary.")

                if not all(isinstance(key, str) for key in action.arguments):
                    raise ValueError("AgentAction argument keys must be strings.")


def validate_benchmark(tasks: tuple[BenchmarkTask, ...]) -> None:
    """Validate a benchmark collection and enforce unique task IDs."""

    if not isinstance(tasks, tuple) or not tasks:
        raise ValueError("Benchmark tasks must be a non-empty tuple.")

    seen_ids: set[str] = set()

    for task in tasks:
        if not isinstance(task, BenchmarkTask):
            raise ValueError("Every benchmark entry must be a BenchmarkTask.")

        if task.task_id in seen_ids:
            raise ValueError(f"Duplicate benchmark task_id: {task.task_id}")

        seen_ids.add(task.task_id)

