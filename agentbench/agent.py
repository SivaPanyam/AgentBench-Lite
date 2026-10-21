
"""Agent execution and bounded recovery for AgentBench Lite."""

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

from agentbench.execution import ToolResult, execute_tool
from agentbench.tools import ToolRegistry


Strategy = Literal["baseline", "recovery"]

AgentStatus = Literal[
    "success",
    "failed",
    "invalid_action",
    "model_error",
    "step_limit",
]

ELIGIBLE_RETRY_ERRORS = {
    "unknown_tool",
    "validation_error",
    "execution_error",
}


@dataclass(frozen=True)
class AgentAction:
    """Represent a proposed tool call."""

    tool_name: str
    arguments: dict[str, Any] = field(default_factory=dict)


class ModelInterface(Protocol):
    """Define how the agent requests model decisions."""

    def next_action(
        self,
        task: str,
        available_tools: list[dict[str, Any]],
        observations: list[dict[str, Any]],
        error_feedback: dict[str, str] | None,
        retries_remaining: int,
    ) -> object:
        """Return the next proposed action."""
        ...


@dataclass
class MockModel:
    """Return predefined decisions for deterministic testing."""

    actions: list[object]
    calls: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        self.actions = list(self.actions)

    def next_action(
        self,
        task: str,
        available_tools: list[dict[str, Any]],
        observations: list[dict[str, Any]],
        error_feedback: dict[str, str] | None,
        retries_remaining: int,
    ) -> object:
        """Return the next scripted action, or None when exhausted."""
        self.calls += 1
        index = self.calls - 1

        if index >= len(self.actions):
            return None

        return self.actions[index]


@dataclass(frozen=True)
class AgentConfig:
    """Configure the strategy and execution limits."""

    strategy: Strategy = "recovery"
    max_steps: int = 5
    max_retries: int = 1

    def __post_init__(self) -> None:
        if self.strategy not in ("baseline", "recovery"):
            raise ValueError(
                "Strategy must be 'baseline' or 'recovery'."
            )

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


@dataclass(frozen=True)
class AttemptRecord:
    """Preserve the outcome of one model decision and its execution."""

    step: int
    tool_name: str | None
    arguments: dict[str, Any] | None
    outcome: str
    tool_result: ToolResult | None
    error: dict[str, str] | None
    corrective_retry: bool
    task_complete: bool


@dataclass(frozen=True)
class AgentResult:
    """Describe the final task outcome and execution history."""

    task: str
    expected_result: Any
    result: Any
    status: AgentStatus
    task_success: bool
    steps: int
    retries_used: int
    history: list[AttemptRecord]


def _type_description(
    expected_type: type | tuple[type, ...],
) -> str:
    """Describe an argument schema without exposing tool internals."""
    types = (
        expected_type
        if isinstance(expected_type, tuple)
        else (expected_type,)
    )
    return " or ".join(item.__name__ for item in types)


def _available_tools(
    registry: ToolRegistry,
) -> list[dict[str, Any]]:
    """Return public tool descriptions and argument schemas."""
    descriptions = []

    for name in registry.list_tools():
        tool = registry.get(name)
        if tool is None:
            continue

        descriptions.append(
            {
                "name": tool.name,
                "description": tool.description,
                "argument_schema": {
                    argument: _type_description(expected_type)
                    for argument, expected_type
                    in tool.argument_schema.items()
                },
            }
        )

    return descriptions


def _valid_action(action: object) -> bool:
    """Check action structure before sending it to the execution layer."""
    return (
        isinstance(action, AgentAction)
        and isinstance(action.tool_name, str)
        and bool(action.tool_name.strip())
        and isinstance(action.arguments, dict)
        and all(isinstance(key, str) for key in action.arguments)
    )


def _results_match(actual: Any, expected: Any) -> bool:
    """Compare results without treating booleans as integers."""
    if isinstance(actual, bool) or isinstance(expected, bool):
        return type(actual) is type(expected) and actual == expected

    return actual == expected


def run_agent(
    task: str,
    expected_result: Any,
    model: ModelInterface,
    registry: ToolRegistry,
    config: AgentConfig | None = None,
) -> AgentResult:
    """Run a task using bounded, optionally recoverable tool execution.

    Task success requires a successful tool result matching expected_result.
    Each model decision consumes one step. Only eligible tool failures can
    trigger a corrective retry.
    """
    if not isinstance(task, str) or not task.strip():
        raise ValueError("task must be a non-empty string.")

    if config is None:
        config = AgentConfig()

    history: list[AttemptRecord] = []
    observations: list[dict[str, Any]] = []
    steps = 0
    retries_used = 0
    error_feedback: dict[str, str] | None = None
    next_is_retry = False
    last_result: Any = None

    available_tools = _available_tools(registry)

    def finish(status: AgentStatus) -> AgentResult:
        return AgentResult(
            task=task,
            expected_result=expected_result,
            result=last_result,
            status=status,
            task_success=(status == "success"),
            steps=steps,
            retries_used=retries_used,
            history=list(history),
        )

    while steps < config.max_steps:
        if next_is_retry:
            retries_used += 1

        corrective_retry = next_is_retry
        next_is_retry = False
        steps += 1

        try:
            action = model.next_action(
                task=task,
                available_tools=available_tools,
                observations=list(observations),
                error_feedback=error_feedback,
                retries_remaining=max(
                    0, config.max_retries - retries_used
                ),
            )
        except Exception:
            error = {
                "code": "model_error",
                "message": "The model interface failed unexpectedly.",
            }
            history.append(
                AttemptRecord(
                    step=steps,
                    tool_name=None,
                    arguments=None,
                    outcome="model_error",
                    tool_result=None,
                    error=error,
                    corrective_retry=corrective_retry,
                    task_complete=False,
                )
            )
            observations.append(
                {
                    "step": steps,
                    "outcome": "model_error",
                    "error": error,
                }
            )
            return finish("model_error")

        if not _valid_action(action):
            error = {
                "code": "malformed_action",
                "message": "The model did not return a valid AgentAction.",
            }
            history.append(
                AttemptRecord(
                    step=steps,
                    tool_name=None,
                    arguments=None,
                    outcome="invalid_action",
                    tool_result=None,
                    error=error,
                    corrective_retry=corrective_retry,
                    task_complete=False,
                )
            )
            observations.append(
                {
                    "step": steps,
                    "outcome": "invalid_action",
                    "error": error,
                }
            )
            return finish("invalid_action")

        tool_name = action.tool_name
        arguments = dict(action.arguments)

        tool_result = execute_tool(registry, tool_name, arguments)
        last_result = tool_result.result

        error = (
            dict(tool_result.error)
            if tool_result.error is not None
            else None
        )

        task_complete = (
            tool_result.success
            and _results_match(tool_result.result, expected_result)
        )

        outcome = (
            "success"
            if task_complete
            else (
                "tool_success_incomplete"
                if tool_result.success
                else (error or {}).get("code", "execution_error")
            )
        )

        history.append(
            AttemptRecord(
                step=steps,
                tool_name=tool_name,
                arguments=arguments,
                outcome=outcome,
                tool_result=tool_result,
                error=error,
                corrective_retry=corrective_retry,
                task_complete=task_complete,
            )
        )

        observation: dict[str, Any] = {
            "step": steps,
            "tool_name": tool_name,
            "arguments": arguments,
            "outcome": outcome,
            "task_complete": task_complete,
        }

        if tool_result.success:
            observation["result"] = tool_result.result
        else:
            observation["error"] = error

        observations.append(observation)
        error_feedback = None

        if task_complete:
            return finish("success")

        if tool_result.success:
            # A successful tool call with the wrong result is not a tool
            # failure. The model may propose another action.
            continue

        error_code = (error or {}).get("code", "")

        retry_eligible = error_code in ELIGIBLE_RETRY_ERRORS
        retry_available = (
            config.strategy == "recovery"
            and retries_used < config.max_retries
        )

        if retry_eligible and retry_available:
            if steps >= config.max_steps:
                return finish("step_limit")

            error_feedback = {
                "code": error_code,
                "message": (error or {}).get(
                    "message", "Tool call failed."
                ),
            }
            next_is_retry = True
            continue

        return finish("failed")

    return finish("step_limit")
