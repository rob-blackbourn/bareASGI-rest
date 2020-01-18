"""Utility functions"""

from datetime import datetime
from decimal import Decimal
from inspect import Parameter, Signature
from typing import (
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar
)

import bareasgi_rest.typing_inspect as typing_inspect
from .json_serialization import underscore_object
from .types import Body

T = TypeVar('T')


class NullIter(Generic[T]):
    """An iterator containing no items"""

    def __aiter__(self):
        return self

    async def __anext__(self) -> T:
        raise StopAsyncIteration


def is_body_type(annotation: Any) -> bool:
    """Determine if the annotation is of type Body[T]

    Args:
        annotation (Any): The annotation

    Returns:
        bool: True if the annotation is of type Body[T], otherwise False
    """
    return typing_inspect.get_origin(annotation) is Body


def get_body_type(annotation: Any) -> Any:
    """Gets the type T of Body[T]

    Args:
        annotation (Any): The annotation

    Returns:
        Any: The type of the body
    """
    body_type, *_rest = typing_inspect.get_args(annotation)
    return body_type


def is_json_container(annotation: Any) -> bool:
    """Return True if this is a JSON container.

    A JSON container can be an object (Like a Dict[str, Any]), or a List.

    Args:
        annotation (Any): The type annotation.

    Returns:
        bool: True if the annotation is represented in JSON as a container.
    """
    if typing_inspect.is_optional_type(annotation):
        return is_json_container(typing_inspect.get_optional(annotation))
    else:
        return (
            typing_inspect.is_list(annotation) or
            typing_inspect.is_dict(annotation) or
            typing_inspect.is_typed_dict(annotation)
        )


def is_json_literal(annoation: Any) -> bool:
    """Return True if the annotation is a JSON literal

    Args:
        annoation (Any): The annotation

    Returns:
        bool: True if the annotation is a JSON literal, otherwise False
    """
    return annoation in (
        str,
        bool,
        int,
        float,
        Decimal,
        datetime
    )


def _from_json_value_to_builtin(value: Any, builtin_type: Type) -> Any:
    if isinstance(value, builtin_type):
        return value
    elif isinstance(value, str):
        if builtin_type is str:
            return value
        elif builtin_type is int:
            return int(value)
        elif builtin_type is bool:
            return value.lower() == 'true'
        elif builtin_type is float:
            return float(value)
        elif builtin_type is Decimal:
            return Decimal(value)
        elif builtin_type is datetime:
            return datetime.fromisoformat(value[:-1])
        else:
            raise TypeError(f'Unhandled type {builtin_type}')
    else:
        raise RuntimeError(f'Unable to coerce value {value}')


def _from_json_value(value: Any, annotation: Any) -> Any:
    if is_json_literal(annotation):
        single_value = value[0] if isinstance(value, list) else value
        return _from_json_value_to_builtin(single_value, annotation)

    if typing_inspect.is_optional_type(annotation):
        optional_type = typing_inspect.get_optional(annotation)
        return None if not value else _from_json_value(value, optional_type)
    elif typing_inspect.is_list(annotation):
        element_type, *_rest = typing_inspect.get_args(annotation)
        return [_from_json_value(item, element_type) for item in value]
    elif typing_inspect.is_dict(annotation):
        return underscore_object(value)
    elif typing_inspect.is_typed_dict(annotation):
        return _from_json_value_to_typed_dict(value, annotation)
    else:
        raise TypeError


def _from_json_value_to_typed_dict(
        values: Optional[Dict[str, Any]],
        annotation: Any
) -> Optional[Dict[str, Any]]:
    if values is None or not typing_inspect.is_typed_dict(annotation):
        return values

    coerced_values: Dict[str, Any] = {}

    member_annotations = typing_inspect.typed_dict_annotation(annotation)
    for name, member in member_annotations.items():
        camelcase_name = camelize(name, False)
        if camelcase_name in values:
            if typing_inspect.is_typed_dict(member.annotation):
                coerced_values[name] = _from_json_value_to_typed_dict(
                    values[camelcase_name],
                    member.annotation
                )
            else:
                coerced_values[name] = _from_json_value(
                    values[camelcase_name],
                    member.annotation
                )
        elif member.default is typing_inspect.TypedDictMember.empty:
            raise KeyError(
                f'Required key "{camelcase_name}" is missing'
            )
        else:
            coerced_values[name] = _from_json_value(
                member.default, member.annotation)

    return coerced_values


def make_args(
        signature: Signature,
        matches: Dict[str, str],
        query: Dict[str, Any],
        body: Dict[str, Any]
) -> Tuple[Tuple[Any, ...], Dict[str, Any]]:
    """Make args and kwargs for the given signature from the route matches,
    query args and body.

    Args:
        signature (Signature): The function signature
        matches (Dict[str, str]): The route matches
        query (Dict[str, Any]): A dictionary built from the query string
        body (Dict[str, Any]): A dictionary built from the body

    Raises:
        KeyError: If a parameter was not found

    Returns:
        Tuple[Tuple[Any, ...], Dict[str, Any]]: A tuple for *args and **kwargs
    """

    kwargs: Dict[str, Any] = {}
    args: List[Any] = []

    body_parameter: Optional[Parameter] = None

    for parameter in signature.parameters.values():
        if is_body_type(parameter.annotation):
            body_type = get_body_type(parameter.annotation)
            value: Any = Body(_from_json_value(body, body_type))
        else:
            camelcase_name = camelize(
                parameter.name, uppercase_first_letter=False)
            if camelcase_name in matches:
                value = _from_json_value(
                    matches[camelcase_name], parameter.annotation)
            elif camelcase_name in query:
                value = _from_json_value(
                    query[camelcase_name], parameter.annotation)
            elif body_parameter is None and camelcase_name in body:
                value = _from_json_value(
                    body[camelcase_name], parameter.annotation)
            elif typing_inspect.is_optional_type(parameter.annotation):
                value = None
            else:
                raise KeyError

        if (
                parameter.kind == Parameter.POSITIONAL_ONLY
                or parameter.kind == Parameter.POSITIONAL_OR_KEYWORD
        ):
            args.append(value)
        else:
            # Use the non-camelcased name
            kwargs[parameter.name] = value

    bound_args = signature.bind(*args, **kwargs)
    bound_args.apply_defaults()

    return bound_args.args, bound_args.kwargs
