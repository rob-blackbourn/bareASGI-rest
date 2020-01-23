"""JSON Serialization"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import (
    Any,
    Dict,
    Optional,
    Type,
    Union
)

import bareasgi_rest.typing_inspect as typing_inspect
from ..iso_8601 import (
    iso_8601_to_datetime,
    iso_8601_to_timedelta
)
from ...utils import rename_object
from ...types import Renamer, Annotation

from ..utils import is_simple_type


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


def from_json_value(
        rename_internal: Renamer,
        rename_external: Renamer,
        value: Any,
        annotation: Annotation,
) -> Any:
    """Convert a JSON value info a Python value

    Args:
        value (Any): The JSON value
        annotation (Any): The Python type annotation
        rename_external (Callable[[str], str]): A function to rename object keys.

    Raises:
        TypeError: If the value cannot be converter

    Returns:
        Any: The Python value
    """
    if is_simple_type(annotation):
        single_value = value[0] if isinstance(value, list) else value
        return _from_json_value_to_builtin(single_value, annotation)

    if typing_inspect.is_optional_type(annotation):
        # An optional is a union where the last element is the None type.
        union_types = typing_inspect.get_args(annotation)[:-1]
        if len(union_types) == 1:
            return None if not value else from_json_value(
                rename_internal,
                rename_external,
                value,
                union_types[0],
            )
        else:
            union = Union[tuple(union_types)]  # type: ignore
            return from_json_value(
                rename_internal,
                rename_external,
                value,
                union,
            )
        optional_type = typing_inspect.get_optional(annotation)
        return None if not value else from_json_value(
            rename_internal,
            rename_external,
            value,
            optional_type,
        )
    elif typing_inspect.is_list(annotation):
        element_type, *_rest = typing_inspect.get_args(annotation)
        return [
            from_json_value(
                rename_internal,
                rename_external,
                item,
                element_type,
            )
            for item in value
        ]
    elif typing_inspect.is_dict(annotation):
        return rename_object(value, rename_internal)
    elif typing_inspect.is_typed_dict(annotation):
        return _from_json_obj_to_typed_dict(
            value,
            annotation,
            rename_internal,
            rename_external
        )
    elif typing_inspect.is_union_type(annotation):
        for arg_annotation in typing_inspect.get_args(annotation):
            try:
                return from_json_value(
                    rename_internal,
                    rename_external,
                    value,
                    arg_annotation,
                )
            except:  # pylint: disable=bare-except
                pass

    raise TypeError


def _from_json_obj_to_typed_dict(
        obj: Optional[Dict[str, Any]],
        annotation: Annotation,
        rename_internal: Renamer,
        rename_external: Renamer
) -> Optional[Dict[str, Any]]:
    if obj is None or not typing_inspect.is_typed_dict(annotation):
        return obj

    coerced_values: Dict[str, Any] = {}

    member_annotations = typing_inspect.typed_dict_annotation(annotation)
    for name, member in member_annotations.items():
        external_name = rename_external(name)
        if external_name in obj:
            if typing_inspect.is_typed_dict(member.annotation):
                coerced_values[name] = _from_json_obj_to_typed_dict(
                    obj[external_name],
                    member.annotation,
                    rename_internal,
                    rename_external
                )
            else:
                coerced_values[name] = from_json_value(
                    rename_internal,
                    rename_external,
                    obj[external_name],
                    member.annotation,
                )
        elif member.default is typing_inspect.TypedDictMember.empty:
            raise KeyError(
                f'Required key "{external_name}" is missing'
            )
        else:
            coerced_values[name] = from_json_value(
                rename_internal,
                rename_external,
                member.default,
                member.annotation,
            )

    return coerced_values
