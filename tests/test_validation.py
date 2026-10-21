
import pytest

from agentbench.validation import validate_arguments


@pytest.fixture
def schema():
    return {"a": int, "b": int}


def test_valid_arguments(schema):
    assert validate_arguments(schema, {"a": 10, "b": 5}) == []


def test_missing_argument(schema):
    errors = validate_arguments(schema, {"a": 10})

    assert [error.code for error in errors] == ["missing_argument"]


def test_unexpected_argument(schema):
    errors = validate_arguments(schema, {"a": 10, "b": 5, "c": 2})

    assert [error.code for error in errors] == ["unexpected_argument"]


def test_invalid_argument_type(schema):
    errors = validate_arguments(schema, {"a": "10", "b": 5})

    assert [error.code for error in errors] == ["invalid_argument_type"]


@pytest.mark.parametrize("value", [True, False])
def test_boolean_rejected_for_numeric_argument(schema, value):
    errors = validate_arguments(schema, {"a": value, "b": 5})

    assert [error.code for error in errors] == ["invalid_argument_type"]


def test_malformed_arguments(schema):
    errors = validate_arguments(schema, ["a", 10])

    assert [error.code for error in errors] == ["invalid_arguments"]


def test_multiple_validation_errors(schema):
    errors = validate_arguments(schema, {"a": "10", "extra": 5})

    assert [error.code for error in errors] == [
        "missing_argument",
        "unexpected_argument",
        "invalid_argument_type",
    ]
