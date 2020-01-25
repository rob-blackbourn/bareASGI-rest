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
    JSONProperty,
    get_json_annotation
)


def _from_json_value_to_builtin(value: Any, type_annotation: Type) -> Any:
    if isinstance(value, type_annotation):
        return value
    elif isinstance(value, str):
        if type_annotation is str:
            return value
        elif type_annotation is int:
            return int(value)
        elif type_annotation is bool:
            return value.lower() == 'true'
        elif type_annotation is float:
            return float(value)
        elif type_annotation is Decimal:
            return Decimal(value)
        elif type_annotation is datetime:
            return iso_8601_to_datetime(value)
        elif type_annotation is timedelta:
            return iso_8601_to_timedelta(value)
        else:
            raise TypeError(f'Unhandled type {type_annotation}')
    else:
        raise RuntimeError(f'Unable to coerce value {value}')


def _from_json_obj_to_optional(
        obj: Any,
        type_annotation: Annotation,
        json_annotation: JSONAnnotation
) -> Any:
    # An optional is a union where the last element is the None type.
    union_types = typing_inspect.get_args(type_annotation)[:-1]
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
    optional_type = typing_inspect.get_optional(type_annotation)
    return None if not obj else _from_json_value(
        obj,
        optional_type,
        json_annotation
    )


def _from_json_obj_to_list(
        lst: list,
        type_annotation: Annotation
) -> Any:
    item_annotation, *_rest = typing_inspect.get_args(type_annotation)
    item_type_annotation, item_json_annotation = get_json_annotation(
        item_annotation
    )

    return [
        _from_json_value(
            item,
            item_type_annotation,
            item_json_annotation
        )
        for item in lst
    ]


def _from_json_obj_to_union(
        obj: Optional[Dict[str, Any]],
        type_annotation: Annotation,
        json_annotation: JSONAnnotation
) -> Any:
    for item_type_annotation in typing_inspect.get_args(type_annotation):
        try:
            return _from_json_value(
                obj,
                item_type_annotation,
                json_annotation
            )
        except:  # pylint: disable=bare-except
            pass


def _from_json_obj_to_typed_dict(
        obj: Dict[str, Any],
        type_annotation: Annotation
) -> Dict[str, Any]:
    json_obj: Dict[str, Any] = {}

    type_annotations = typing_inspect.typed_dict_annotation(type_annotation)
    for name, member in type_annotations.items():
        item_type_annotation, item_json_annotation = get_json_annotation(
            member.annotation
        )
        if not issubclass(type(item_json_annotation), JSONProperty):
            raise TypeError("Must be a property")
        json_property = cast(JSONProperty, item_json_annotation)

        if json_property.tag in obj:
            json_obj[name] = _from_json_value(
                obj[json_property.tag],
                item_type_annotation,
                item_json_annotation
            )
        elif typing_inspect.is_optional_type(item_type_annotation):
            json_obj[name] = None
        elif member.default is typing_inspect.TypedDictMember.empty:
            raise KeyError(
                f'Required key "{json_property.tag}" is missing'
            )
        else:
            json_obj[name] = _from_json_value(
                member.default,
                item_type_annotation,
                item_json_annotation
            )

    return json_obj


def _from_json_value(
        json_value: Any,
        type_annotation: Annotation,
        json_annotation: JSONAnnotation
) -> Any:
    if is_simple_type(type_annotation):
        return _from_json_value_to_builtin(
            json_value,
            type_annotation
        )
    elif typing_inspect.is_optional_type(type_annotation):
        return _from_json_obj_to_optional(
            json_value,
            type_annotation,
            json_annotation
        )
    elif typing_inspect.is_list(type_annotation):
        return _from_json_obj_to_list(
            json_value,
            type_annotation
        )
    elif typing_inspect.is_typed_dict(type_annotation):
        return _from_json_obj_to_typed_dict(
            json_value,
            type_annotation
        )
    elif typing_inspect.is_union_type(type_annotation):
        return _from_json_obj_to_union(
            json_value,
            type_annotation,
            json_annotation
        )
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
    type_annotation, json_annotation = get_json_annotation(annotation)
    if not isinstance(json_annotation, JSONValue):
        raise TypeError(
            "Expected the root value to have a JSONValue annotation"
        )

    json_value = json.loads(text)
    return _from_json_value(
        json_value,
        type_annotation,
        json_annotation
    )
