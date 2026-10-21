
"""Tests for the AgentBench Lite agent controller."""

import pytest

from agentbench.agent import (
    AgentAction,
    AgentConfig,
    MockModel,
    run_agent,
)
from agentbench.execution import create_default_registry


def request_action(model):
    """Call the mock model using the expected interface."""
    return model.next_action(
        task="Calculate 10 + 5",
        available_tools=[],
        observations=[],
        error_feedback=None,
        retries_remaining=1,
    )


def test_agent_action_stores_tool_and_arguments():
    action = AgentAction(
        tool_name="calculator",
        arguments={"a": 10, "b": 5, "operation": "add"},
    )

    assert action.tool_name == "calculator"
    assert action.arguments == {
        "a": 10,
        "b": 5,
        "operation": "add",
    }


def test_agent_action_defaults_to_empty_arguments():
    action = AgentAction(tool_name="mock_lookup")

    assert action.arguments == {}


def test_mock_model_returns_actions_in_order():
    first = AgentAction("calculator", {"a": 10})
    second = AgentAction("mock_lookup", {"key": "python"})
    model = MockModel(actions=[first, second])

    assert request_action(model) == first
    assert request_action(model) == second
    assert model.calls == 2


def test_mock_model_returns_malformed_response_for_testing():
    model = MockModel(actions=["malformed"])

    assert request_action(model) == "malformed"


def test_mock_model_returns_none_when_actions_are_exhausted():
    model = MockModel(actions=[AgentAction("calculator")])

    request_action(model)

    assert request_action(model) is None
    assert model.calls == 2


def test_mock_model_copies_input_action_sequence():
    actions = [AgentAction("calculator")]
    model = MockModel(actions=actions)

    actions.append(AgentAction("mock_lookup"))

    assert request_action(model) == AgentAction("calculator")
    assert request_action(model) is None


def test_default_agent_config():
    config = AgentConfig()

    assert config.strategy == "recovery"
    assert config.max_steps == 5
    assert config.max_retries == 1


@pytest.mark.parametrize("strategy", ["baseline", "recovery"])
def test_agent_config_accepts_supported_strategies(strategy):
    assert AgentConfig(strategy=strategy).strategy == strategy


@pytest.mark.parametrize("strategy", ["invalid", "", None])
def test_agent_config_rejects_invalid_strategy(strategy):
    with pytest.raises(ValueError, match="Strategy"):
        AgentConfig(strategy=strategy)


@pytest.mark.parametrize("max_steps", [0, -1, True, 1.5, "5"])
def test_agent_config_rejects_invalid_step_limits(max_steps):
    with pytest.raises(ValueError, match="max_steps"):
        AgentConfig(max_steps=max_steps)


@pytest.mark.parametrize("max_retries", [-1, 2, True, 1.5, "1"])
def test_agent_config_rejects_invalid_retry_limits(max_retries):
    with pytest.raises(ValueError, match="max_retries"):
        AgentConfig(max_retries=max_retries)


def test_agent_config_allows_zero_retries():
    config = AgentConfig(max_retries=0)

    assert config.max_retries == 0


def test_agent_config_is_immutable():
    config = AgentConfig()

    with pytest.raises(AttributeError):
        config.max_steps = 10


def test_agent_completes_task_with_expected_result():
    model = MockModel(
        actions=[
            AgentAction(
                "calculator",
                {"a": 10, "b": 5, "operation": "add"},
            )
        ]
    )

    result = run_agent(
        task="Calculate 10 + 5",
        expected_result=15,
        model=model,
        registry=create_default_registry(),
    )

    assert result.status == "success"
    assert result.task_success is True
    assert result.result == 15
    assert result.steps == 1
    assert len(result.history) == 1
    assert result.history[0].task_complete is True


def test_successful_tool_call_with_wrong_result_is_not_task_success():
    model = MockModel(
        actions=[
            AgentAction(
                "calculator",
                {"a": 2, "b": 3, "operation": "add"},
            ),
            AgentAction(
                "calculator",
                {"a": 8, "b": 8, "operation": "add"},
            ),
        ]
    )

    result = run_agent(
        task="Calculate a result of 16",
        expected_result=16,
        model=model,
        registry=create_default_registry(),
    )

    assert result.status == "success"
    assert result.result == 16
    assert result.steps == 2
    assert result.history[0].outcome == "tool_success_incomplete"
    assert result.history[1].task_complete is True


def test_baseline_does_not_retry_unknown_tool():
    model = MockModel(
        actions=[
            AgentAction("missing_tool", {}),
            AgentAction(
                "calculator",
                {"a": 10, "b": 5, "operation": "add"},
            ),
        ]
    )

    result = run_agent(
        task="Calculate 10 + 5",
        expected_result=15,
        model=model,
        registry=create_default_registry(),
        config=AgentConfig(strategy="baseline"),
    )

    assert result.status == "failed"
    assert result.steps == 1
    assert result.retries_used == 0
    assert model.calls == 1
    assert result.history[0].error["code"] == "unknown_tool"


def test_recovery_succeeds_after_corrective_retry():
    model = MockModel(
        actions=[
            AgentAction("missing_tool", {}),
            AgentAction(
                "calculator",
                {"a": 10, "b": 5, "operation": "add"},
            ),
        ]
    )

    result = run_agent(
        task="Calculate 10 + 5",
        expected_result=15,
        model=model,
        registry=create_default_registry(),
    )

    assert result.status == "success"
    assert result.task_success is True
    assert result.steps == 2
    assert result.retries_used == 1
    assert len(result.history) == 2
    assert result.history[0].outcome == "unknown_tool"
    assert result.history[0].corrective_retry is False
    assert result.history[1].corrective_retry is True


def test_validation_failure_can_be_corrected():
    model = MockModel(
        actions=[
            AgentAction("calculator", {"a": 10}),
            AgentAction(
                "calculator",
                {"a": 10, "b": 5, "operation": "add"},
            ),
        ]
    )

    result = run_agent(
        task="Calculate 10 + 5",
        expected_result=15,
        model=model,
        registry=create_default_registry(),
    )

    assert result.status == "success"
    assert result.history[0].error["code"] == "validation_error"
    assert result.retries_used == 1


def test_execution_failure_can_be_corrected():
    model = MockModel(
        actions=[
            AgentAction(
                "calculator",
                {"a": 10, "b": 0, "operation": "divide"},
            ),
            AgentAction(
                "calculator",
                {"a": 10, "b": 5, "operation": "divide"},
            ),
        ]
    )

    result = run_agent(
        task="Divide 10 by 5",
        expected_result=2.0,
        model=model,
        registry=create_default_registry(),
    )

    assert result.status == "success"
    assert result.history[0].error["code"] == "execution_error"
    assert result.history[1].tool_result.result == 2.0
    assert result.retries_used == 1


def test_second_failure_terminates_recovery():
    model = MockModel(
        actions=[
            AgentAction("missing_tool", {}),
            AgentAction("another_missing_tool", {}),
        ]
    )

    result = run_agent(
        task="Run a tool",
        expected_result=None,
        model=model,
        registry=create_default_registry(),
    )

    assert result.status == "failed"
    assert result.retries_used == 1
    assert result.steps == 2
    assert len(result.history) == 2
    assert model.calls == 2


def test_malformed_action_returns_structured_failure():
    model = MockModel(actions=["not an action"])

    result = run_agent(
        task="Calculate 10 + 5",
        expected_result=15,
        model=model,
        registry=create_default_registry(),
    )

    assert result.status == "invalid_action"
    assert result.task_success is False
    assert result.history[0].outcome == "invalid_action"
    assert result.history[0].error["code"] == "malformed_action"
    assert model.calls == 1


def test_model_exception_returns_safe_structured_failure():
    class FailingModel:
        def next_action(self, **kwargs):
            raise RuntimeError("private implementation detail")

    result = run_agent(
        task="Calculate 10 + 5",
        expected_result=15,
        model=FailingModel(),
        registry=create_default_registry(),
    )

    assert result.status == "model_error"
    assert result.task_success is False
    assert result.history[0].error["code"] == "model_error"
    assert "private implementation detail" not in (
        result.history[0].error["message"]
    )


def test_step_limit_stops_repeated_incomplete_actions():
    model = MockModel(
        actions=[
            AgentAction(
                "calculator",
                {"a": 1, "b": 1, "operation": "add"},
            ),
            AgentAction(
                "calculator",
                {"a": 2, "b": 2, "operation": "add"},
            ),
            AgentAction(
                "calculator",
                {"a": 3, "b": 3, "operation": "add"},
            ),
        ]
    )

    result = run_agent(
        task="Calculate a result of 100",
        expected_result=100,
        model=model,
        registry=create_default_registry(),
        config=AgentConfig(max_steps=2),
    )

    assert result.status == "step_limit"
    assert result.steps == 2
    assert len(result.history) == 2
    assert model.calls == 2


def test_recovery_cannot_exceed_step_limit():
    model = MockModel(actions=[AgentAction("missing_tool", {})])

    result = run_agent(
        task="Run a tool",
        expected_result=1,
        model=model,
        registry=create_default_registry(),
        config=AgentConfig(max_steps=1, max_retries=1),
    )

    assert result.status == "step_limit"
    assert result.steps == 1
    assert result.retries_used == 0
    assert model.calls == 1


def test_model_is_not_called_again_after_task_success():
    model = MockModel(
        actions=[
            AgentAction(
                "calculator",
                {"a": 10, "b": 5, "operation": "add"},
            ),
            AgentAction("missing_tool", {}),
        ]
    )

    result = run_agent(
        task="Calculate 10 + 5",
        expected_result=15,
        model=model,
        registry=create_default_registry(),
    )

    assert result.status == "success"
    assert model.calls == 1
    assert result.steps == 1


def test_empty_task_is_rejected():
    model = MockModel(actions=[])

    with pytest.raises(ValueError, match="non-empty"):
        run_agent(
            task=" ",
            expected_result=15,
            model=model,
            registry=create_default_registry(),
        )

    assert model.calls == 0


# ---------------------------------------------------------
# Additional Phase 3 regression tests
# ---------------------------------------------------------


def test_boolean_does_not_match_integer_expected_result():
    model = MockModel(
        actions=[
            AgentAction(
                "calculator",
                {"a": 0, "b": 1, "operation": "add"},
            )
        ]
    )

    result = run_agent(
        task="Calculate zero plus one",
        expected_result=True,
        model=model,
        registry=create_default_registry(),
    )

    # The calculator returns integer 1, not Boolean True.
    # The exhausted mock subsequently returns None, which is invalid.
    assert result.status == "invalid_action"
    assert result.task_success is False
    assert result.result == 1
    assert result.history[0].task_complete is False


def test_model_receives_error_feedback_and_remaining_retry_budget():
    class RecordingModel:
        def __init__(self):
            self.calls = []

        def next_action(
            self,
            task,
            available_tools,
            observations,
            error_feedback,
            retries_remaining,
        ):
            self.calls.append(
                {
                    "error_feedback": error_feedback,
                    "retries_remaining": retries_remaining,
                    "observations": observations,
                }
            )

            if len(self.calls) == 1:
                return AgentAction("unknown_tool")

            return AgentAction(
                "calculator",
                {"a": 1, "b": 1, "operation": "add"},
            )

    model = RecordingModel()

    result = run_agent(
        task="Calculate one plus one",
        expected_result=2,
        model=model,
        registry=create_default_registry(),
        config=AgentConfig(strategy="recovery", max_retries=1),
    )

    assert result.status == "success"
    assert result.retries_used == 1
    assert len(model.calls) == 2

    assert model.calls[0]["error_feedback"] is None
    assert model.calls[0]["retries_remaining"] == 1

    assert model.calls[1]["error_feedback"]["code"] == "unknown_tool"
    assert model.calls[1]["retries_remaining"] == 0
    assert model.calls[1]["observations"][0]["outcome"] == "unknown_tool"


def test_malformed_action_during_retry_is_recorded():
    model = MockModel(
        actions=[
            AgentAction("unknown_tool"),
            None,
        ]
    )

    result = run_agent(
        task="Calculate two",
        expected_result=2,
        model=model,
        registry=create_default_registry(),
        config=AgentConfig(strategy="recovery", max_retries=1),
    )

    assert result.status == "invalid_action"
    assert result.task_success is False
    assert result.steps == 2
    assert result.retries_used == 1
    assert len(result.history) == 2

    assert result.history[0].error["code"] == "unknown_tool"
    assert result.history[1].outcome == "invalid_action"
    assert result.history[1].corrective_retry is True


def test_final_allowed_step_does_not_make_an_extra_model_call():
    model = MockModel(
        actions=[
            AgentAction(
                "calculator",
                {"a": 1, "b": 1, "operation": "add"},
            ),
            AgentAction(
                "calculator",
                {"a": 2, "b": 2, "operation": "add"},
            ),
        ]
    )

    result = run_agent(
        task="Calculate a result of 100",
        expected_result=100,
        model=model,
        registry=create_default_registry(),
        config=AgentConfig(max_steps=1),
    )

    assert result.status == "step_limit"
    assert result.steps == 1
    assert model.calls == 1
    assert len(result.history) == 1
