
import pytest

from agentbench.execution import (
    ToolResult,
    create_default_registry,
    execute_tool,
)
from agentbench.tools import Tool, ToolRegistry


@pytest.fixture
def registry():
    return create_default_registry()


def test_calculator_execution_succeeds(registry):
    result = execute_tool(
        registry,
        "calculator",
        {"a": 10, "b": 5, "operation": "add"},
    )

    assert result.success is True
    assert result.tool_name == "calculator"
    assert result.result == 15
    assert result.error is None


def test_unit_converter_execution_succeeds(registry):
    result = execute_tool(
        registry,
        "unit_converter",
        {"value": 10, "from_unit": "km", "to_unit": "miles"},
    )

    assert result.success is True
    assert result.result == 6.2137
    assert result.error is None


def test_mock_lookup_execution_succeeds(registry):
    result = execute_tool(registry, "mock_lookup", {"key": "python"})

    assert result.success is True
    assert result.result["name"] == "Python"
    assert result.error is None


def test_unknown_tool_is_rejected(registry):
    result = execute_tool(registry, "missing", {})

    assert result.success is False
    assert result.tool_name == "missing"
    assert result.result is None
    assert result.error["code"] == "unknown_tool"


def test_non_string_tool_name_is_rejected(registry):
    result = execute_tool(registry, 123, {})

    assert result.success is False
    assert result.tool_name == "123"
    assert result.error["code"] == "unknown_tool"


def test_missing_argument_is_rejected(registry):
    result = execute_tool(registry, "calculator", {"a": 10})

    assert result.success is False
    assert result.result is None
    assert result.error["code"] == "validation_error"


def test_unexpected_argument_is_rejected(registry):
    result = execute_tool(
        registry,
        "calculator",
        {"a": 10, "b": 5, "operation": "add", "extra": 1},
    )

    assert result.success is False
    assert result.result is None
    assert result.error["code"] == "validation_error"
    assert "Unexpected argument: extra" in result.error["message"]


def test_non_dictionary_arguments_are_rejected(registry):
    result = execute_tool(registry, "calculator", ["not", "a", "dictionary"])

    assert result.success is False
    assert result.result is None
    assert result.error["code"] == "validation_error"
    assert "dictionary" in result.error["message"].lower()


def test_boolean_numeric_argument_is_rejected(registry):
    result = execute_tool(
        registry,
        "calculator",
        {"a": True, "b": 5, "operation": "add"},
    )

    assert result.success is False
    assert result.error["code"] == "validation_error"


def test_unsupported_operation_is_execution_error(registry):
    result = execute_tool(
        registry,
        "calculator",
        {"a": 10, "b": 5, "operation": "power"},
    )

    assert result.success is False
    assert result.result is None
    assert result.error["code"] == "execution_error"


def test_division_by_zero_is_execution_error(registry):
    result = execute_tool(
        registry,
        "calculator",
        {"a": 10, "b": 0, "operation": "divide"},
    )

    assert result.success is False
    assert result.result is None
    assert result.error["code"] == "execution_error"
    assert "divide by zero" in result.error["message"].lower()


def test_unknown_lookup_key_is_execution_error(registry):
    result = execute_tool(registry, "mock_lookup", {"key": "unknown_entry"})

    assert result.success is False
    assert result.result is None
    assert result.error["code"] == "execution_error"


def test_unsupported_unit_conversion_is_execution_error(registry):
    result = execute_tool(
        registry,
        "unit_converter",
        {"value": 10, "from_unit": "kg", "to_unit": "miles"},
    )

    assert result.success is False
    assert result.result is None
    assert result.error["code"] == "execution_error"


def test_invalid_arguments_do_not_execute_tool():
    calls = []
    custom_registry = ToolRegistry()

    def probe(value):
        calls.append(value)
        return value

    custom_registry.register(
        Tool(
            name="probe",
            description="Test validation before execution.",
            argument_schema={"value": int},
            function=probe,
        )
    )

    result = execute_tool(custom_registry, "probe", {"value": "invalid"})

    assert result.success is False
    assert result.error["code"] == "validation_error"
    assert calls == []


def test_unexpected_exception_is_captured_safely():
    custom_registry = ToolRegistry()

    def failing_tool(value: int):
        raise RuntimeError("internal implementation detail")

    custom_registry.register(
        Tool(
            name="failing_tool",
            description="Tool that raises an unexpected exception.",
            argument_schema={"value": int},
            function=failing_tool,
        )
    )

    result = execute_tool(
        custom_registry,
        "failing_tool",
        {"value": 1},
    )

    assert result.success is False
    assert result.result is None
    assert result.error["code"] == "execution_error"
    assert result.error["message"] == (
        "An unexpected error occurred during tool execution."
    )
    assert "internal implementation detail" not in result.error["message"]


def test_success_result_has_consistent_structure(registry):
    result = execute_tool(
        registry,
        "calculator",
        {"a": 2, "b": 3, "operation": "add"},
    )

    assert isinstance(result, ToolResult)
    assert result.success is True
    assert result.tool_name == "calculator"
    assert result.result == 5
    assert result.error is None


def test_failure_result_has_consistent_structure(registry):
    result = execute_tool(registry, "unknown_tool", {})

    assert isinstance(result, ToolResult)
    assert result.success is False
    assert result.tool_name == "unknown_tool"
    assert result.result is None
    assert isinstance(result.error, dict)
    assert set(result.error) == {"code", "message"}
