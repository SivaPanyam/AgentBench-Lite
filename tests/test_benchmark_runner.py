
"""Tests for the AgentBench Lite benchmark runner."""

import json

import pytest

from agentbench.agent import AgentAction
from agentbench.benchmark import BenchmarkTask
from agentbench.benchmark_runner import (
    _expected_status_for_strategy,
    _run_one_task,
    run_benchmark,
)


@pytest.fixture
def recovery_task():
    """A task where recovery succeeds after an initial tool failure."""
    return BenchmarkTask(
        task_id="test_recovery",
        description="Recover from a missing tool and add two numbers.",
        category="recovery_success",
        actions=(
            AgentAction("missing_tool", {}),
            AgentAction(
                "calculator",
                {"operation": "add", "a": 2, "b": 3},
            ),
        ),
        expected_result=5,
        expected_status="success",
    )


@pytest.fixture
def simple_task():
    """A successful task that does not require recovery."""
    return BenchmarkTask(
        task_id="test_add",
        description="Add two numbers.",
        category="calculator",
        actions=(
            AgentAction(
                "calculator",
                {"operation": "add", "a": 4, "b": 6},
            ),
        ),
        expected_result=10,
        expected_status="success",
    )


def test_expected_status_differs_for_recovery_task(recovery_task):
    assert _expected_status_for_strategy(
        recovery_task, "baseline"
    ) == "failed"

    assert _expected_status_for_strategy(
        recovery_task, "recovery"
    ) == "success"


def test_expected_status_for_regular_task_is_unchanged(simple_task):
    assert _expected_status_for_strategy(
        simple_task, "baseline"
    ) == "success"

    assert _expected_status_for_strategy(
        simple_task, "recovery"
    ) == "success"


def test_baseline_does_not_recover(recovery_task):
    record = _run_one_task(recovery_task, "baseline")

    assert record["actual_status"] == "failed"
    assert record["expected_status"] == "failed"
    assert record["expected_status_match"] is True
    assert record["task_success"] is False
    assert record["retries_used"] == 0


def test_recovery_completes_recovery_task(recovery_task):
    record = _run_one_task(recovery_task, "recovery")

    assert record["actual_status"] == "success"
    assert record["expected_status"] == "success"
    assert record["expected_status_match"] is True
    assert record["task_success"] is True
    assert record["retries_used"] == 1
    assert record["actual_result"] == 5


def test_simple_task_succeeds_under_both_strategies(simple_task):
    for strategy in ("baseline", "recovery"):
        record = _run_one_task(simple_task, strategy)

        assert record["actual_status"] == "success"
        assert record["expected_status_match"] is True
        assert record["task_success"] is True
        assert record["retries_used"] == 0


def test_run_benchmark_writes_json_files(
    simple_task,
    tmp_path,
):
    report = run_benchmark(
        (simple_task,),
        output_dir=tmp_path,
        run_id="test_json",
    )

    results_path = tmp_path / "benchmark_results_test_json.json"
    summary_path = tmp_path / "benchmark_summary_test_json.json"

    assert results_path.exists()
    assert summary_path.exists()

    results_data = json.loads(results_path.read_text(encoding="utf-8"))
    summary_data = json.loads(summary_path.read_text(encoding="utf-8"))

    assert len(results_data["results"]) == 2
    assert summary_data["summary"]["task_count"] == 1
    assert report["task_count"] == 1


def test_summary_metrics_for_simple_task(simple_task, tmp_path):
    report = run_benchmark(
        (simple_task,),
        output_dir=tmp_path,
        run_id="test_metrics",
    )

    summary = report["summary"]

    assert summary["strategies"]["baseline"]["completed_tasks"] == 1
    assert summary["strategies"]["recovery"]["completed_tasks"] == 1
    assert summary["strategies"]["baseline"]["total_retries"] == 0
    assert summary["strategies"]["recovery"]["total_retries"] == 0
    assert summary["comparison"]["completion_rate_difference"] == 0.0
    assert summary["comparison"]["status_mismatches"] == 0


def test_existing_output_is_not_overwritten(simple_task, tmp_path):
    run_benchmark(
        (simple_task,),
        output_dir=tmp_path,
        run_id="protected_run",
    )

    results_path = tmp_path / "benchmark_results_protected_run.json"
    original_content = results_path.read_text(encoding="utf-8")

    with pytest.raises(FileExistsError):
        run_benchmark(
            (simple_task,),
            output_dir=tmp_path,
            run_id="protected_run",
        )

    assert results_path.read_text(encoding="utf-8") == original_content


def test_overwrite_must_be_explicit(simple_task, tmp_path):
    run_benchmark(
        (simple_task,),
        output_dir=tmp_path,
        run_id="overwrite_run",
    )

    report = run_benchmark(
        (simple_task,),
        output_dir=tmp_path,
        run_id="overwrite_run",
        overwrite=True,
    )

    assert report["task_count"] == 1


@pytest.mark.parametrize(
    "run_id",
    [
        "",
        "../unsafe",
        "bad run",
        "run.json",
    ],
)
def test_invalid_run_id_is_rejected(simple_task, tmp_path, run_id):
    with pytest.raises(ValueError):
        run_benchmark(
            (simple_task,),
            output_dir=tmp_path,
            run_id=run_id,
        )


def test_empty_benchmark_is_rejected(tmp_path):
    with pytest.raises(ValueError):
        run_benchmark((), output_dir=tmp_path, run_id="empty")


def test_invalid_task_entry_is_rejected(tmp_path):
    with pytest.raises(ValueError):
        run_benchmark(
            ("not a benchmark task",),
            output_dir=tmp_path,
            run_id="invalid",
        )
