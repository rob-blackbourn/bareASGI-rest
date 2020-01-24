"""JSON Serialization"""

from datetime import datetime, timedelta
from decimal import Decimal
import json
from typing import (
    Any,
    Dict,
    Optional,
    Type,
    Union,
    cast
)

import bareasgi_rest.typing_inspect as typing_inspect
from ..iso_8601 import (
    iso_8601_to_datetime,
    iso_8601_to_timedelta
)
from ...types import Annotation

from ..utils import is_simple_type
from .annotations import (
    JSONAnnotation,
    JSONValue,
    JSONObject,
    JSONList,
    JSONProperty,
    get_json_annotation
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


def _from_json_obj_to_optional(
        obj: list,
        annotation: Annotation,
        json_annotation: JSONAnnotation
) -> Any:
    # An optional is a union where the last element is the None type.
    union_types = typing_inspect.get_args(annotation)[:-1]
    if len(union_types) == 1:
        return None if not obj else _from_json_value(
            obj,
            union_types[0],
            json_annotation
        )
    else:
        union = Union[tuple(union_types)]  # type: ignore
        return _from_json_value(
            obj,
            union,
            json_annotation
        )
    optional_type = typing_inspect.get_optional(annotation)
    return None if not obj else _from_json_value(
        obj,
        optional_type,
        json_annotation
    )


def _from_json_obj_to_list(
        obj: list,
        annotation: Annotation
) -> Any:
    element_annotation, *_rest = typing_inspect.get_args(annotation)
    element_type, element_json_annotation = get_json_annotation(
        element_annotation
    )

    return [
        _from_json_value(
            item,
            element_type,
            element_json_annotation
        )
        for item in obj
    ]


def _from_json_obj_to_union(
        obj: Optional[Dict[str, Any]],
        annotation: Annotation,
        json_annotation: JSONAnnotation
) -> Any:
    for arg_annotation in typing_inspect.get_args(annotation):
        try:
            return _from_json_value(
                obj,
                arg_annotation,
                json_annotation
            )
        except:  # pylint: disable=bare-except
            pass


def _from_json_obj_to_typed_dict(
        obj: Optional[Dict[str, Any]],
        annotation: Annotation
) -> Optional[Dict[str, Any]]:
    if obj is None or not typing_inspect.is_typed_dict(annotation):
        return obj

    json_obj: Dict[str, Any] = {}

    member_annotations = typing_inspect.typed_dict_annotation(annotation)
    for name, member in member_annotations.items():
        member_type, json_annotation = get_json_annotation(member.annotation)
        if not issubclass(type(json_annotation), JSONProperty):
            raise TypeError("Must be a property")

        if cast(JSONProperty, json_annotation).tag in obj:
            json_obj[name] = _from_json_value(
                obj[cast(JSONProperty, json_annotation).tag],
                member_type,
                json_annotation
            )
        elif typing_inspect.is_optional_type(member_type):
            json_obj[name] = None
        elif member.default is typing_inspect.TypedDictMember.empty:
            raise KeyError(
                f'Required key "{json_annotation}" is missing'
            )
        else:
            json_obj[name] = _from_json_value(
                member.default,
                member_type,
                json_annotation
            )

    return json_obj


def _from_json_value(
        obj: Any,
        annotation: Annotation,
        json_annotation: JSONAnnotation
) -> Any:
    if is_simple_type(annotation):
        return _from_json_value_to_builtin(obj, annotation)
    elif typing_inspect.is_optional_type(annotation):
        return _from_json_obj_to_optional(obj, annotation, json_annotation)
    elif typing_inspect.is_list(annotation):
        return _from_json_obj_to_list(obj, annotation)
    # elif typing_inspect.is_dict(annotation):
    #     return rename_object(value, rename_internal)
    elif typing_inspect.is_typed_dict(annotation):
        return _from_json_obj_to_typed_dict(obj, annotation)
    elif typing_inspect.is_union_type(annotation):
        return _from_json_obj_to_union(obj, annotation, json_annotation)
    else:
        raise TypeError


def deserialize(
        text: str,
        annotation: Annotation
) -> Any:
    """Convert JSON to an object

    Args:
        text (str): The JSON string
        annotation (str): The type annotation

    Returns:
        Any: The deserialized object.
    """
    element_type, json_annotation = get_json_annotation(annotation)
    if not isinstance(json_annotation, JSONValue):
        raise TypeError(
            "Expected the root value to have a JSONObject or JSONList annotation"
        )

    obj = json.loads(text)
    return _from_json_value(
        obj,
        element_type,
        json_annotation
    )
