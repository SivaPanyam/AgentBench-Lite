
from dataclasses import dataclass
from typing import Any, Callable


ArgumentType = type | tuple[type, ...]


@dataclass(frozen=True)
class Tool:
    """Describe a registered tool and its expected arguments."""

    name: str
    description: str
    argument_schema: dict[str, ArgumentType]
    function: Callable[..., Any]


class ToolRegistry:
    """Store and retrieve tools by their unique names."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool after checking its basic definition."""

        if not isinstance(tool, Tool):
            raise TypeError("Only Tool instances can be registered.")

        if not isinstance(tool.name, str) or not tool.name.strip():
            raise ValueError("Tool name must be a non-empty string.")

        if not isinstance(tool.description, str):
            raise TypeError("Tool description must be a string.")

        if not isinstance(tool.argument_schema, dict):
            raise TypeError("Tool argument schema must be a dictionary.")

        if not callable(tool.function):
            raise TypeError("Tool function must be callable.")

        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")

        for argument, expected_type in tool.argument_schema.items():
            if not isinstance(argument, str) or not argument:
                raise ValueError("Argument names must be non-empty strings.")

            accepted_types = (
                expected_type
                if isinstance(expected_type, tuple)
                else (expected_type,)
            )

            if not accepted_types or not all(
                isinstance(item, type) for item in accepted_types
            ):
                raise TypeError(
                    f"Expected type for argument '{argument}' "
                    "must be a type or a tuple of types."
                )

        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        """Return a registered tool, or None if it does not exist."""

        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        """Return registered tool names in registration order."""

        return list(self._tools.keys())


def calculator(
    a: int | float,
    b: int | float,
    operation: str,
) -> int | float:
    """Perform addition, subtraction, multiplication, or division."""

    for name, value in (("a", a), ("b", b)):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(
                f"Argument '{name}' must be a number, not a boolean."
            )

    if not isinstance(operation, str):
        raise TypeError("Argument 'operation' must be a string.")

    operations = {
        "add": lambda: a + b,
        "subtract": lambda: a - b,
        "multiply": lambda: a * b,
        "divide": lambda: a / b,
    }

    if operation not in operations:
        raise ValueError(f"Unsupported operation: {operation}")

    if operation == "divide" and b == 0:
        raise ZeroDivisionError("Cannot divide by zero.")

    return operations[operation]()


def unit_converter(
    value: int | float,
    from_unit: str,
    to_unit: str,
) -> float:
    """Convert supported distance and temperature units.

    Results are rounded to four decimal places.
    """

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("Argument 'value' must be numeric, not a boolean.")

    if not isinstance(from_unit, str) or not isinstance(to_unit, str):
        raise TypeError("Unit names must be strings.")

    conversions = {
        ("km", "miles"): lambda x: x * 0.621371,
        ("miles", "km"): lambda x: x / 0.621371,
        ("celsius", "fahrenheit"): lambda x: (x * 9 / 5) + 32,
        ("fahrenheit", "celsius"): lambda x: (x - 32) * 5 / 9,
    }

    conversion = conversions.get((from_unit, to_unit))

    if conversion is None:
        raise ValueError(
            f"Unsupported conversion: {from_unit} to {to_unit}"
        )

    return round(conversion(value), 4)


MOCK_DATA = {
    "python": {
        "name": "Python",
        "type": "programming_language",
        "year": 1991,
    },
    "java": {
        "name": "Java",
        "type": "programming_language",
        "year": 1995,
    },
    "pytest": {
        "name": "pytest",
        "type": "testing_framework",
        "year": 2004,
    },
}


def mock_lookup(key: str) -> dict[str, Any]:
    """Look up an entry in the local mock dataset."""

    if not isinstance(key, str):
        raise TypeError("Argument 'key' must be a string.")

    if not key.strip():
        raise ValueError("Lookup key cannot be empty.")

    normalized_key = key.strip().lower()

    if normalized_key not in MOCK_DATA:
        raise KeyError(f"Unknown lookup key: {key}")

    return MOCK_DATA[normalized_key].copy()
