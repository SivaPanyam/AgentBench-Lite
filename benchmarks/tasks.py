
"""Deterministic benchmark tasks for AgentBench Lite."""

from agentbench.agent import AgentAction
from agentbench.benchmark import BenchmarkTask, validate_benchmark


BENCHMARK_TASKS: tuple[BenchmarkTask, ...] = (
    # ---------------------------------------------------------
    # Calculator: successful operations
    # ---------------------------------------------------------
    BenchmarkTask(
        task_id="calc_001",
        description="Add two numbers.",
        category="calculator",
        actions=(AgentAction("calculator", {"operation": "add", "a": 4, "b": 6}),),
        expected_result=10,
        expected_status="success",
    ),
    BenchmarkTask(
        task_id="calc_002",
        description="Subtract two numbers.",
        category="calculator",
        actions=(AgentAction("calculator", {"operation": "subtract", "a": 9, "b": 3}),),
        expected_result=6,
        expected_status="success",
    ),
    BenchmarkTask(
        task_id="calc_003",
        description="Multiply two numbers.",
        category="calculator",
        actions=(AgentAction("calculator", {"operation": "multiply", "a": 7, "b": 8}),),
        expected_result=56,
        expected_status="success",
    ),
    BenchmarkTask(
        task_id="calc_004",
        description="Divide two numbers.",
        category="calculator",
        actions=(AgentAction("calculator", {"operation": "divide", "a": 20, "b": 4}),),
        expected_result=5,
        expected_status="success",
    ),
    BenchmarkTask(
        task_id="calc_005",
        description="Divide by zero.",
        category="execution_failure",
        actions=(AgentAction("calculator", {"operation": "divide", "a": 10, "b": 0}),),
        expected_result=None,
        expected_status="failed",
        max_retries=0,
    ),
    BenchmarkTask(
        task_id="calc_006",
        description="Add a negative and a positive number.",
        category="calculator",
        actions=(AgentAction("calculator", {"operation": "add", "a": -5, "b": 8}),),
        expected_result=3,
        expected_status="success",
    ),
    BenchmarkTask(
        task_id="calc_007",
        description="Subtract a negative number.",
        category="calculator",
        actions=(AgentAction("calculator", {"operation": "subtract", "a": 4, "b": -3}),),
        expected_result=7,
        expected_status="success",
    ),
    BenchmarkTask(
        task_id="calc_008",
        description="Multiply by zero.",
        category="calculator",
        actions=(AgentAction("calculator", {"operation": "multiply", "a": 9, "b": 0}),),
        expected_result=0,
        expected_status="success",
    ),
    BenchmarkTask(
        task_id="calc_009",
        description="Add decimal values.",
        category="calculator",
        actions=(AgentAction("calculator", {"operation": "add", "a": 1.5, "b": 2.5}),),
        expected_result=4.0,
        expected_status="success",
    ),

    # ---------------------------------------------------------
    # Unit conversion: supported distance and temperature units
    # ---------------------------------------------------------
    BenchmarkTask(
        task_id="unit_001",
        description="Convert kilometers to miles.",
        category="unit_conversion",
        actions=(
            AgentAction(
                "unit_converter",
                {"value": 2, "from_unit": "km", "to_unit": "miles"},
            ),
        ),
        expected_result=1.2427,
        expected_status="success",
    ),
    BenchmarkTask(
        task_id="unit_002",
        description="Convert miles to kilometers.",
        category="unit_conversion",
        actions=(
            AgentAction(
                "unit_converter",
                {"value": 5, "from_unit": "miles", "to_unit": "km"},
            ),
        ),
        expected_result=8.0467,
        expected_status="success",
    ),
    BenchmarkTask(
        task_id="unit_003",
        description="Convert Celsius to Fahrenheit.",
        category="unit_conversion",
        actions=(
            AgentAction(
                "unit_converter",
                {
                    "value": 0,
                    "from_unit": "celsius",
                    "to_unit": "fahrenheit",
                },
            ),
        ),
        expected_result=32.0,
        expected_status="success",
    ),
    BenchmarkTask(
        task_id="unit_004",
        description="Convert Fahrenheit to Celsius.",
        category="unit_conversion",
        actions=(
            AgentAction(
                "unit_converter",
                {
                    "value": 212,
                    "from_unit": "fahrenheit",
                    "to_unit": "celsius",
                },
            ),
        ),
        expected_result=100.0,
        expected_status="success",
    ),

    # ---------------------------------------------------------
    # Mock lookup: expected results are complete dictionaries
    # ---------------------------------------------------------
    BenchmarkTask(
        task_id="lookup_001",
        description="Look up Python.",
        category="mock_lookup",
        actions=(AgentAction("mock_lookup", {"key": "python"}),),
        expected_result={
            "name": "Python",
            "type": "programming_language",
            "year": 1991,
        },
        expected_status="success",
    ),
    BenchmarkTask(
        task_id="lookup_002",
        description="Look up Java.",
        category="mock_lookup",
        actions=(AgentAction("mock_lookup", {"key": "java"}),),
        expected_result={
            "name": "Java",
            "type": "programming_language",
            "year": 1995,
        },
        expected_status="success",
    ),

    # ---------------------------------------------------------
    # Tool selection and failures
    # ---------------------------------------------------------
    BenchmarkTask(
        task_id="toolselect_001",
        description="Select calculator to compute a sum.",
        category="tool_selection",
        actions=(AgentAction("calculator", {"operation": "add", "a": 11, "b": 12}),),
        expected_result=23,
        expected_status="success",
    ),
    BenchmarkTask(
        task_id="tool_001",
        description="Call a nonexistent tool.",
        category="unknown_tool",
        actions=(AgentAction("nonexistent_tool", {}),),
        expected_result=None,
        expected_status="failed",
        max_retries=0,
    ),
    BenchmarkTask(
        task_id="tool_002",
        description="Call an unregistered tool.",
        category="unknown_tool",
        actions=(AgentAction("missing_tool", {}),),
        expected_result=None,
        expected_status="failed",
        max_retries=0,
    ),

    # ---------------------------------------------------------
    # Argument validation and execution failures
    # ---------------------------------------------------------
    BenchmarkTask(
        task_id="validation_001",
        description="Call calculator with an unsupported operation.",
        category="execution_failure",
        actions=(
            AgentAction(
                "calculator",
                {"operation": "power", "a": 2, "b": 3},
            ),
        ),
        expected_result=None,
        expected_status="failed",
        max_retries=0,
    ),
    BenchmarkTask(
        task_id="validation_002",
        description="Call calculator with a missing argument.",
        category="validation_failure",
        actions=(AgentAction("calculator", {"operation": "add", "a": 2}),),
        expected_result=None,
        expected_status="failed",
        max_retries=0,
    ),
    BenchmarkTask(
        task_id="validation_003",
        description="Call calculator with a missing operand.",
        category="validation_failure",
        actions=(AgentAction("calculator", {"operation": "subtract", "b": 2}),),
        expected_result=None,
        expected_status="failed",
        max_retries=0,
    ),

    # ---------------------------------------------------------
    # Malformed model actions
    # ---------------------------------------------------------
    BenchmarkTask(
        task_id="malformed_001",
        description="Return a malformed agent action.",
        category="malformed_action",
        actions=("not an AgentAction",),
        expected_result=None,
        expected_status="invalid_action",
    ),
    BenchmarkTask(
        task_id="malformed_002",
        description="Return a null action.",
        category="malformed_action",
        actions=(None,),
        expected_result=None,
        expected_status="invalid_action",
    ),

    # ---------------------------------------------------------
    # Recovery success: first action fails, corrective action works
    # ---------------------------------------------------------
    BenchmarkTask(
        task_id="recovery_001",
        description="Recover from an unknown tool and then add numbers.",
        category="recovery_success",
        actions=(
            AgentAction("nonexistent_tool", {}),
            AgentAction("calculator", {"operation": "add", "a": 2, "b": 5}),
        ),
        expected_result=7,
        expected_status="success",
    ),
    BenchmarkTask(
        task_id="recovery_002",
        description="Recover from invalid arguments and then multiply numbers.",
        category="recovery_success",
        actions=(
            AgentAction("calculator", {"operation": "multiply", "a": 2}),
            AgentAction("calculator", {"operation": "multiply", "a": 3, "b": 4}),
        ),
        expected_result=12,
        expected_status="success",
    ),
    BenchmarkTask(
        task_id="recovery_004",
        description="Recover from an execution error and then add numbers.",
        category="recovery_success",
        actions=(
            AgentAction("calculator", {"operation": "divide", "a": 5, "b": 0}),
            AgentAction("calculator", {"operation": "add", "a": 6, "b": 7}),
        ),
        expected_result=13,
        expected_status="success",
    ),

    # ---------------------------------------------------------
    # Recovery failure: the corrective action fails too
    # ---------------------------------------------------------
    BenchmarkTask(
        task_id="recovery_003",
        description="Retry an unknown tool but fail again.",
        category="recovery_failure",
        actions=(
            AgentAction("nonexistent_tool", {}),
            AgentAction("another_nonexistent_tool", {}),
        ),
        expected_result=None,
        expected_status="failed",
    ),
    BenchmarkTask(
        task_id="recovery_005",
        description="Fail after the corrective action also fails.",
        category="recovery_failure",
        actions=(
            AgentAction("calculator", {"operation": "divide", "a": 5, "b": 0}),
            AgentAction("calculator", {"operation": "divide", "a": 8, "b": 0}),
        ),
        expected_result=None,
        expected_status="failed",
    ),

    # ---------------------------------------------------------
    # Step limits and retry exhaustion
    # ---------------------------------------------------------
    BenchmarkTask(
        task_id="limit_001",
        description="Reach the step limit before completing the task.",
        category="step_limit",
        actions=(
            AgentAction("calculator", {"operation": "add", "a": 1, "b": 1}),
            AgentAction("calculator", {"operation": "add", "a": 2, "b": 2}),
        ),
        expected_result=4,
        expected_status="step_limit",
        max_steps=1,
        max_retries=0,
    ),
    BenchmarkTask(
        task_id="retry_001",
        description="Fail without corrective retries.",
        category="retry_exhaustion",
        actions=(AgentAction("nonexistent_tool", {}),),
        expected_result=None,
        expected_status="failed",
        max_retries=0,
    ),
    BenchmarkTask(
        task_id="retry_002",
        description="Fail on an unknown tool without retries.",
        category="retry_exhaustion",
        actions=(AgentAction("missing_tool", {}),),
        expected_result=None,
        expected_status="failed",
        max_retries=0,
    ),
)


# Validate task IDs, categories, action sequences, and configuration.
validate_benchmark(BENCHMARK_TASKS)
