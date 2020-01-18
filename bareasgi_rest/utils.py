"""Utility functions"""

from datetime import datetime
from decimal import Decimal
from inspect import Parameter, Signature
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    cast
)

from inflection import camelize, underscore

import bareasgi_rest.typing_inspect as typing_inspect
from .types import Body

T = TypeVar('T')  # pylint: disable=invalid-name


def _rename_dict(dct: Dict[str, Any], rename: Callable[[str], str]) -> Dict[str, Any]:
    return {
        rename(name): _rename_object(obj, rename)
        for name, obj in dct.items()
    }


def _rename_list(lst: List[Any], rename: Callable[[str], str]) -> List[Any]:
    return [_rename_object(obj, rename) for obj in lst]


def _rename_object(obj: T, rename: Callable[[str], str]) -> T:
    if isinstance(obj, dict):
        return cast(T, _rename_dict(cast(Dict[str, Any], obj), rename))
    elif isinstance(obj, list):
        return cast(T, _rename_list(cast(List[Any], obj), rename))
    else:
        return obj


def _camelize(text: str) -> str:
    return camelize(text, uppercase_first_letter=False)


def camelize_object(obj: T) -> T:
    """Convert any dictionary keys in the object to camelcase

    :param obj: The object
    :type obj: T
    :return: The object with keys converted to camelcase
    :rtype: T
    """
    return _rename_object(obj, _camelize)


def underscore_object(obj: T) -> T:
    """Convert any dictionary keys in the object to underscore

    :param obj: The object
    :type obj: T
    :return: The object with keys converted to underscore
    :rtype: T
    """
    return _rename_object(obj, underscore)


class NullIter(Generic[T]):
    """An iterator containing no items"""

    def __aiter__(self):
        return self

    async def __anext__(self) -> T:
        raise StopAsyncIteration


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


def _is_supported_optional(annotation) -> bool:
    return (
        annotation is Optional[str] or
        annotation is Optional[bool] or
        annotation is Optional[int] or
        annotation is Optional[float] or
        annotation is Optional[Decimal] or
        annotation is Optional[datetime]
    )


def _coerce_builtin(value: Any, builtin_type: Type) -> Any:
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


def _coerce(value: Any, annotation: Any) -> Any:
    if is_json_literal(annotation):
        single_value = value[0] if isinstance(value, list) else value
        return _coerce_builtin(single_value, annotation)

    if typing_inspect.is_optional_type(annotation):
        optional_type = typing_inspect.get_optional(annotation)
        return None if not value else _coerce(value, optional_type)
    elif typing_inspect.is_list(annotation):
        element_type, *_rest = typing_inspect.get_args(annotation)
        return [_coerce(item, element_type) for item in value]
    elif typing_inspect.is_dict(annotation):
        return value
    elif typing_inspect.is_typed_dict(annotation):
        return _update_defaults(value, annotation)
    else:
        raise TypeError


def _is_typed_dict_callable(signature: Signature) -> bool:
    if len(signature.parameters) != 1:
        return False
    parameter = next(iter(signature.parameters.values()))
    return typing_inspect.is_typed_dict(parameter.annotation)


def _update_defaults(
        values: Optional[Dict[str, Any]],
        annotation: Any
) -> Optional[Dict[str, Any]]:
    if values is None or not typing_inspect.is_typed_dict(annotation):
        return values

    member_annotations = typing_inspect.typed_dict_annotation(annotation)
    for name, member in member_annotations.items():
        if name in values:
            if typing_inspect.is_typed_dict(member.annotation):
                _update_defaults(values[name], member.annotation)
            else:
                values[name] = _coerce(values[name], member.annotation)
        elif member.default is typing_inspect.TypedDictMember.empty:
            raise KeyError(f'Required argument "{name}" is missing')
        else:
            values[name] = _coerce(member.default, member.annotation)

    return values


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
            value = Body(_coerce(body, body_type))
        else:
            camcelcase_name = camelize(
                parameter.name, uppercase_first_letter=False)
            if camcelcase_name in matches:
                value = _coerce(matches[camcelcase_name], parameter.annotation)
            elif camcelcase_name in query:
                value = _coerce(query[camcelcase_name], parameter.annotation)
            elif body_parameter is None and camcelcase_name in body:
                value = _coerce(body[camcelcase_name], parameter.annotation)
            elif _is_supported_optional(parameter.annotation):
                continue
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


def is_body_type(annotation: Any) -> bool:
    return typing_inspect.get_origin(annotation) is Body


def get_body_type(annotation: Any) -> Any:
    body_type, *_rest = typing_inspect.get_args(annotation)
    return body_type
