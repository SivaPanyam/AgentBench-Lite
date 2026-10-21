
from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationError:
    """Describe a tool argument validation failure."""

    code: str
    message: str


def validate_arguments(
    argument_schema: dict[str, type | tuple[type, ...]],
    arguments: object,
) -> list[ValidationError]:
    """Validate arguments against a tool's declared schema."""

    if not isinstance(arguments, dict):
        return [
            ValidationError(
                code="invalid_arguments",
                message="Arguments must be provided as a dictionary.",
            )
        ]

    errors: list[ValidationError] = []
    expected_names = set(argument_schema)
    provided_names = set(arguments)

    for name in sorted(expected_names - provided_names):
        errors.append(
            ValidationError(
                code="missing_argument",
                message=f"Missing required argument: {name}",
            )
        )

    for name in sorted(provided_names - expected_names, key=str):
        errors.append(
            ValidationError(
                code="unexpected_argument",
                message=f"Unexpected argument: {name}",
            )
        )

    for name in sorted(expected_names & provided_names):
        expected_type = argument_schema[name]
        value = arguments[name]
        accepted_types = (
            expected_type if isinstance(expected_type, tuple)
            else (expected_type,)
        )

        if (
            any(item in (int, float) for item in accepted_types)
            and isinstance(value, bool)
        ):
            valid_type = False
        else:
            valid_type = isinstance(value, accepted_types)

        if not valid_type:
            type_names = " or ".join(item.__name__ for item in accepted_types)
            errors.append(
                ValidationError(
                    code="invalid_argument_type",
                    message=f"Argument '{name}' must be {type_names}.",
                )
            )

    return errors
