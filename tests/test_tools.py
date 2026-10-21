
import pytest

from agentbench.tools import calculator, mock_lookup, unit_converter


# Calculator tests

@pytest.mark.parametrize(
    ("a", "b", "operation", "expected"),
    [
        (10, 5, "add", 15),
        (10, 5, "subtract", 5),
        (10, 5, "multiply", 50),
        (10, 5, "divide", 2.0),
        (2.5, 1.5, "add", 4.0),
        (-10, 5, "multiply", -50),
    ],
)
def test_calculator_operations(a, b, operation, expected):
    assert calculator(a, b, operation) == expected


def test_calculator_division_by_zero():
    with pytest.raises(ZeroDivisionError, match="Cannot divide by zero"):
        calculator(10, 0, "divide")


def test_calculator_unsupported_operation():
    with pytest.raises(ValueError, match="Unsupported operation"):
        calculator(10, 5, "power")


@pytest.mark.parametrize("value", [True, False, "10", None, []])
def test_calculator_rejects_invalid_numeric_arguments(value):
    with pytest.raises(TypeError):
        calculator(value, 5, "add")


def test_calculator_rejects_invalid_second_argument():
    with pytest.raises(TypeError):
        calculator(10, "5", "add")


def test_calculator_rejects_non_string_operation():
    with pytest.raises(TypeError, match="operation"):
        calculator(10, 5, 1)


# Unit converter tests

@pytest.mark.parametrize(
    ("value", "from_unit", "to_unit", "expected"),
    [
        (10, "km", "miles", 6.2137),
        (10, "miles", "km", 16.0934),
        (0, "celsius", "fahrenheit", 32.0),
        (100, "celsius", "fahrenheit", 212.0),
        (32, "fahrenheit", "celsius", 0.0),
        (212, "fahrenheit", "celsius", 100.0),
    ],
)
def test_unit_converter_supported_conversions(
    value, from_unit, to_unit, expected
):
    assert unit_converter(value, from_unit, to_unit) == expected


def test_unit_converter_unsupported_conversion():
    with pytest.raises(ValueError, match="Unsupported conversion"):
        unit_converter(10, "km", "celsius")


@pytest.mark.parametrize("value", [True, False, "10", None, []])
def test_unit_converter_rejects_invalid_values(value):
    with pytest.raises(TypeError):
        unit_converter(value, "km", "miles")


def test_unit_converter_rejects_non_string_units():
    with pytest.raises(TypeError, match="Unit names must be strings"):
        unit_converter(10, "km", 5)


def test_unit_converter_rounds_to_four_decimal_places():
    assert unit_converter(1, "km", "miles") == 0.6214


# Mock lookup tests

@pytest.mark.parametrize(
    ("key", "expected_name", "expected_type", "expected_year"),
    [
        ("python", "Python", "programming_language", 1991),
        ("java", "Java", "programming_language", 1995),
        ("pytest", "pytest", "testing_framework", 2004),
    ],
)
def test_mock_lookup_known_keys(key, expected_name, expected_type, expected_year):
    result = mock_lookup(key)

    assert result == {
        "name": expected_name,
        "type": expected_type,
        "year": expected_year,
    }


def test_mock_lookup_is_case_insensitive():
    assert mock_lookup("PYTHON") == mock_lookup("python")


def test_mock_lookup_strips_surrounding_whitespace():
    assert mock_lookup("  java  ") == mock_lookup("java")


def test_mock_lookup_unknown_key():
    with pytest.raises(KeyError, match="Unknown lookup key"):
        mock_lookup("unknown")


def test_mock_lookup_rejects_empty_key():
    with pytest.raises(ValueError, match="cannot be empty"):
        mock_lookup("   ")


@pytest.mark.parametrize("key", [True, 123, None, [], {}])
def test_mock_lookup_rejects_non_string_keys(key):
    with pytest.raises(TypeError, match="must be a string"):
        mock_lookup(key)


def test_mock_lookup_does_not_allow_mutation_of_stored_data():
    result = mock_lookup("python")
    result["name"] = "Modified"

    assert mock_lookup("python")["name"] == "Python"
