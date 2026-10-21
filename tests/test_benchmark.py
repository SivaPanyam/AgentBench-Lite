
"""Tests for benchmark task definitions and validation."""

import pytest

from agentbench.agent import AgentAction
from agentbench.benchmark import BenchmarkTask, validate_benchmark


def make_task(task_id="task-001", **overrides):
    values = {
        "task_id": task_id,
        "description": "Calculate ten plus five.",
        "category": "calculator",
        "actions": (
            AgentAction(
                "calculator",
                {"a": 10, "b": 5, "operation": "add"},
            ),
        ),
        "expected_result": 15,
        "expected_status": "success",
    }
    values.update(overrides)
    return BenchmarkTask(**values)


def test_valid_benchmark_task():
    task = make_task()

    assert task.task_id == "task-001"
    assert task.expected_result == 15
    assert task.expected_status == "success"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("task_id", ""),
        ("description", " "),
        ("category", "unsupported"),
        ("actions", ()),
        ("expected_status", "unknown"),
        ("max_steps", 0),
        ("max_steps", True),
        ("max_retries", 2),
        ("max_retries", True),
        ("tags", ("valid", "")),
    ],
)
def test_invalid_task_definitions_are_rejected(field, value):
    with pytest.raises(ValueError):
        make_task(**{field: value})


def test_benchmark_requires_non_empty_tuple():
    with pytest.raises(ValueError, match="non-empty tuple"):
        validate_benchmark(())


def test_benchmark_rejects_duplicate_ids():
    tasks = (make_task(), make_task())

    with pytest.raises(ValueError, match="Duplicate"):
        validate_benchmark(tasks)


def test_benchmark_accepts_unique_ids():
    tasks = (
        make_task("task-001"),
        make_task("task-002"),
    )

    validate_benchmark(tasks)


def test_benchmark_rejects_non_task_entries():
    with pytest.raises(ValueError, match="BenchmarkTask"):
        validate_benchmark(("not a task",))


def test_malformed_model_action_can_be_represented():
    task = make_task(actions=("malformed response",))

    assert task.actions == ("malformed response",)
