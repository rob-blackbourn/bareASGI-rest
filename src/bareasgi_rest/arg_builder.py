"""Argument builder"""

from inspect import Parameter, Signature
from typing import Any, Awaitable, Callable, get_args

from jetblack_serialization.custom_annotations import (
    is_any_serialization_annotation
)

from jetblack_serialization import typing_ex

from .types import ArgDeserializer


def is_optional_list(annotation: Any) -> bool:
    if not typing_ex.is_optional(annotation):
        return False
    optional_types = typing_ex.get_optional_types(annotation)
    if len(optional_types) != 1:
        return False
    return typing_ex.is_list(optional_types[0])


async def make_args(
        signature: Signature,
        matches: dict[str, str],
        query: dict[str, list[str]],
        body: Callable[[Any], Awaitable[Any]],
        arg_deserializer: ArgDeserializer
) -> tuple[tuple[Any, ...], dict[str, Any]]:
    """Make args and kwargs for the given signature from the route matches,
    query args and body.

    Args:
        signature (Signature): The function signature
        matches (dict[str, str]): The route matches
        query (dict[str, Any]): A dictionary built from the query string
        body (Callable[[AsyncIterator[bytes], Any], Any]): Get the body
        arg_deserializer (ArgDeserializer): A deserializer for args

    Raises:
        KeyError: If a parameter was not found

    Returns:
        tuple[tuple[Any, ...], dict[str, Any]]: A tuple for *args and **kwargs
    """

    kwargs: dict[str, Any] = {}
    args: list[Any] = []

    for parameter in signature.parameters.values():
        if is_any_serialization_annotation(parameter.annotation):
            value: Any = await body(parameter.annotation)
        else:
            if parameter.name in matches:
                value = arg_deserializer(
                    matches[parameter.name],
                    parameter.annotation
                )
            elif parameter.name in query:
                if typing_ex.is_list(
                        parameter.annotation
                ) or is_optional_list(
                    parameter.annotation
                ):
                    element_type, *_rest = get_args(parameter.annotation)
                    value = [
                        arg_deserializer(item, element_type)
                        for item in query[parameter.name]
                    ]
                else:
                    value = arg_deserializer(
                        query[parameter.name][0],
                        parameter.annotation
                    )

            elif typing_ex.is_optional(parameter.annotation):
                value = None
            else:
                raise KeyError(parameter.name)

        if (
                parameter.kind == Parameter.POSITIONAL_ONLY
                or parameter.kind == Parameter.POSITIONAL_OR_KEYWORD
        ):
            args.append(value)
        else:
            kwargs[parameter.name] = value

    bound_args = signature.bind(*args, **kwargs)
    bound_args.apply_defaults()

    return bound_args.args, bound_args.kwargs
