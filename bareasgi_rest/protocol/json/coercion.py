"""Serialization"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
    cast
)

from inflection import camelize, underscore

import bareasgi_rest.typing_inspect as typing_inspect
from ..iso_8601 import (
    iso_8601_to_datetime,
    iso_8601_to_timedelta
)

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


def _camelize(value: Any) -> Any:
    return camelize(value, False) if isinstance(value, str) else value


def camelize_object(obj: T) -> T:
    """Convert any dictionary keys in the object to camelcase

    :param obj: The object
    :type obj: T
    :return: The object with keys converted to camelcase
    :rtype: T
    """
    return _rename_object(obj, _camelize)


def _underscore(value: Any) -> Any:
    return underscore(value) if isinstance(value, str) else value


def underscore_object(obj: T) -> T:
    """Convert any dictionary keys in the object to underscore

    :param obj: The object
    :type obj: T
    :return: The object with keys converted to underscore
    :rtype: T
    """
    return _rename_object(obj, _underscore)


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
        datetime,
        timedelta
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
            return iso_8601_to_datetime(value)
        elif builtin_type is timedelta:
            return iso_8601_to_timedelta(value)
        else:
            raise TypeError(f'Unhandled type {builtin_type}')
    else:
        raise RuntimeError(f'Unable to coerce value {value}')


def from_json_value(value: Any, annotation: Any) -> Any:
    """Convert a JSON value info a Python value

    Args:
        value (Any): The JSON value
        annotation (Any): The Python type annotation

    Raises:
        TypeError: If the value cannot be converter

    Returns:
        Any: The Python value
    """
    if is_json_literal(annotation):
        single_value = value[0] if isinstance(value, list) else value
        return _from_json_value_to_builtin(single_value, annotation)

    if typing_inspect.is_optional_type(annotation):
        # An optional is a union where the last element is the None type.
        union_types = typing_inspect.get_args(annotation)[:-1]
        if len(union_types) == 1:
            return None if not value else from_json_value(value, union_types[0])
        else:
            union = Union[tuple(union_types)]  # type: ignore
            return from_json_value(value, union)
        optional_type = typing_inspect.get_optional(annotation)
        return None if not value else from_json_value(value, optional_type)
    elif typing_inspect.is_list(annotation):
        element_type, *_rest = typing_inspect.get_args(annotation)
        return [from_json_value(item, element_type) for item in value]
    elif typing_inspect.is_dict(annotation):
        return underscore_object(value)
    elif typing_inspect.is_typed_dict(annotation):
        return _from_json_value_to_typed_dict(value, annotation)
    elif typing_inspect.is_union_type(annotation):
        for arg_annotation in typing_inspect.get_args(annotation):
            try:
                return from_json_value(value, arg_annotation)
            except:  # pylint: disable=bare-except
                pass

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
                coerced_values[name] = from_json_value(
                    values[camelcase_name],
                    member.annotation
                )
        elif member.default is typing_inspect.TypedDictMember.empty:
            raise KeyError(
                f'Required key "{camelcase_name}" is missing'
            )
        else:
            coerced_values[name] = from_json_value(
                member.default, member.annotation)

    return coerced_values
