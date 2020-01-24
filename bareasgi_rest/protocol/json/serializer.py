"""An XML serializer"""

from datetime import datetime, timedelta
from decimal import Decimal
import json
from typing import Any, Optional, Type, Union, cast

import bareasgi_rest.typing_inspect as typing_inspect
from ...types import Annotation
from ..utils import is_simple_type
from ..iso_8601 import (
    datetime_to_iso_8601,
    timedelta_to_iso_8601
)

from .annotations import (
    JSONAnnotation,
    JSONValue,
    JSONObject,
    JSONList,
    JSONProperty,
    get_json_annotation
)


def _simple_type_to_json_obj(
        obj: Any,
        element_type: Type
) -> str:
    if element_type is str:
        return obj
    elif element_type is int:
        return obj
    elif element_type is bool:
        return obj
    elif element_type is float:
        return obj
    elif element_type is Decimal:
        return obj
    elif element_type is datetime:
        return datetime_to_iso_8601(obj)
    elif element_type is timedelta:
        return timedelta_to_iso_8601(obj)
    else:
        raise TypeError(f'Unhandled type {element_type}')


def _from_optional_obj_to_json(
        obj: Any,
        element_type: Annotation,
        json_annotation: JSONAnnotation,
) -> Any:
    if obj is None:
        return None

    # An optional is a union where the last element is the None type.
    union_types = typing_inspect.get_args(element_type)[:-1]
    if len(union_types) == 1:
        # This was Optional[T]
        return _from_obj_to_json(
            obj,
            union_types[0],
            json_annotation,
        )
    else:
        return _from_union_obj_to_json(
            obj,
            Union[tuple(union_types)],
            json_annotation,
        )


def _from_union_obj_to_json(
        obj: Any,
        annotation: Annotation,
        json_annotation: JSONAnnotation,
) -> Any:
    for element_type in typing_inspect.get_args(annotation):
        try:
            return _from_obj_to_json(
                obj,
                element_type,
                json_annotation,
            )
        except:  # pylint: disable=bare-except
            pass


def _from_list_to_json(
        obj: list,
        annotation: Annotation,
) -> Any:
    element_annotation, *_rest = typing_inspect.get_args(annotation)
    element_type, element_json_annotation = get_json_annotation(
        element_annotation
    )

    return [
        _from_obj_to_json(
            item,
            element_type,
            element_json_annotation
        )
        for item in obj
    ]


def _from_typed_dict_to_json(
        obj: dict,
        annotation: Annotation,
) -> dict:
    json_obj = dict()

    member_annotations = typing_inspect.typed_dict_annotation(annotation)
    for name, member in member_annotations.items():
        member_type, member_json_annotation = get_json_annotation(
            member.annotation
        )
        if not issubclass(type(member_json_annotation), JSONProperty):
            raise TypeError("<ust be a property")
        json_property = cast(JSONProperty, member_json_annotation)

        json_obj[json_property.tag] = _from_obj_to_json(
            obj.get(name),
            member_type,
            member_json_annotation,
        )
    return json_obj


def _from_simple_to_json(
        obj: Any,
        element_type: Annotation,
        json_annotation: JSONAnnotation,
) -> Any:
    return _simple_type_to_json_obj(obj, element_type)


def _from_obj_to_json(
        obj: Any,
        element_type: Annotation,
        json_annotation: JSONAnnotation,
) -> Any:
    if is_simple_type(element_type):
        return _from_simple_to_json(obj, element_type, json_annotation)
    elif typing_inspect.is_optional_type(element_type):
        return _from_optional_obj_to_json(obj, element_type, json_annotation)
    elif typing_inspect.is_list(element_type):
        return _from_list_to_json(obj, element_type)
    elif typing_inspect.is_typed_dict(element_type):
        return _from_typed_dict_to_json(obj, element_type)
    elif typing_inspect.is_union_type(element_type):
        return _from_union_obj_to_json(obj, element_type, json_annotation)
    else:
        raise TypeError


def serialize(obj: Any, annotation: Annotation) -> str:
    element_type, json_annotation = get_json_annotation(annotation)
    if not isinstance(json_annotation, JSONValue):
        raise TypeError(
            "Expected the root value to have an JSONValue annotation")

    json_obj = _from_obj_to_json(obj, element_type, json_annotation)
    return json.dumps(json_obj)
