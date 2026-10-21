
from dataclasses import dataclass
from typing import Any

from agentbench.tools import (
    Tool,
    ToolRegistry,
    calculator,
    mock_lookup,
    unit_converter,
)
from agentbench.validation import validate_arguments


@dataclass(frozen=True)
class ToolResult:
    """Represent a consistent tool execution result."""

    success: bool
    tool_name: str
    result: Any = None
    error: dict[str, str] | None = None


def create_default_registry() -> ToolRegistry:
    """Create a registry containing all built-in tools."""

    registry = ToolRegistry()

    registry.register(
        Tool(
            name="calculator",
            description="Perform basic arithmetic operations.",
            argument_schema={
                "a": (int, float),
                "b": (int, float),
                "operation": str,
            },
            function=calculator,
        )
    )

    registry.register(
        Tool(
            name="unit_converter",
            description="Convert supported distance and temperature units.",
            argument_schema={
                "value": (int, float),
                "from_unit": str,
                "to_unit": str,
            },
            function=unit_converter,
        )
    )

    registry.register(
        Tool(
            name="mock_lookup",
            description="Look up an entry in the local mock dataset.",
            argument_schema={"key": str},
            function=mock_lookup,
        )
    )

    return registry


def execute_tool(
    registry: ToolRegistry,
    tool_name: str,
    arguments: object,
) -> ToolResult:
    """Validate and execute a registered tool safely."""

    if not isinstance(tool_name, str):
        return ToolResult(
            success=False,
            tool_name=str(tool_name),
            error={
                "code": "unknown_tool",
                "message": f"Unknown tool: {tool_name}",
            },
        )

    tool = registry.get(tool_name)

    if tool is None:
        return ToolResult(
            success=False,
            tool_name=tool_name,
            error={
                "code": "unknown_tool",
                "message": f"Unknown tool: {tool_name}",
            },
        )

    errors = validate_arguments(tool.argument_schema, arguments)

    if errors:
        return ToolResult(
            success=False,
            tool_name=tool_name,
            error={
                "code": "validation_error",
                "message": "; ".join(error.message for error in errors),
            },
        )

    try:
        result = tool.function(**arguments)
        return ToolResult(
            success=True,
            tool_name=tool_name,
            result=result,
        )
    except (TypeError, ValueError, ZeroDivisionError, KeyError) as error:
        return ToolResult(
            success=False,
            tool_name=tool_name,
            error={
                "code": "execution_error",
                "message": str(error),
            },
        )
    except Exception:
        return ToolResult(
            success=False,
            tool_name=tool_name,
            error={
                "code": "execution_error",
                "message": "An unexpected error occurred during tool execution.",
            },
        )
