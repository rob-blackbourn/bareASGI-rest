"""An XML serializer"""

from datetime import datetime, timedelta
from decimal import Decimal
import json
from typing import Any, Type, Union, cast

import bareasgi_rest.typing_inspect as typing_inspect
from ..config import SerializerConfig
from ...types import Annotation
from ..utils import is_simple_type
from ..iso_8601 import (
    datetime_to_iso_8601,
    timedelta_to_iso_8601
)

from .annotations import (
    JSONAnnotation,
    JSONValue,
    JSONProperty,
    get_json_annotation
)


def _from_optional_obj_to_json(
        obj: Any,
        type_annotation: Annotation,
        json_annotation: JSONAnnotation,
        config: SerializerConfig
) -> Any:
    if obj is None:
        return None

    # An optional is a union where the last element is the None type.
    union_types = typing_inspect.get_args(type_annotation)[:-1]
    if len(union_types) == 1:
        # This was Optional[T]
        return _from_value_to_json(
            obj,
            union_types[0],
            json_annotation,
            config
        )
    else:
        return _from_union_obj_to_json(
            obj,
            Union[tuple(union_types)],
            json_annotation,
            config
        )


def _from_union_obj_to_json(
        obj: Any,
        type_annotation: Annotation,
        json_annotation: JSONAnnotation,
        config: SerializerConfig
) -> Any:
    for element_type in typing_inspect.get_args(type_annotation):
        try:
            return _from_value_to_json(
                obj,
                element_type,
                json_annotation,
                config
            )
        except:  # pylint: disable=bare-except
            pass


def _from_list_to_json(
        lst: list,
        type_annotation: Annotation,
        config: SerializerConfig
) -> Any:
    item_annotation, *_rest = typing_inspect.get_args(type_annotation)
    item_type_annotation, item_json_annotation = get_json_annotation(
        item_annotation
    )

    return [
        _from_value_to_json(
            item,
            item_type_annotation,
            item_json_annotation,
            config
        )
        for item in lst
    ]


def _from_typed_dict_to_json(
        dct: dict,
        type_annotation: Annotation,
        config: SerializerConfig
) -> dict:
    json_obj = dict()

    item_annotations = typing_inspect.typed_dict_annotation(type_annotation)
    for name, member in item_annotations.items():
        if typing_inspect.is_annotated_type(member.annotation):
            item_type_annotation, item_json_annotation = get_json_annotation(
                member.annotation
            )
            if not issubclass(type(item_json_annotation), JSONProperty):
                raise TypeError("<ust be a property")
            json_property = cast(JSONProperty, item_json_annotation)
        else:
            property_name = config.serialize_key(
                name
            ) if config.serialize_key and isinstance(name, str) else name
            json_property = JSONProperty(property_name)

        json_obj[json_property.tag] = _from_value_to_json(
            dct.get(name),
            item_type_annotation,
            json_property,
            config
        )
    return json_obj


def _from_simple_to_json(
        obj: Any,
        type_annotation: Type
) -> Any:
    if type_annotation is str:
        return obj
    elif type_annotation is int:
        return obj
    elif type_annotation is bool:
        return obj
    elif type_annotation is float:
        return obj
    elif type_annotation is Decimal:
        return obj
    elif type_annotation is datetime:
        return datetime_to_iso_8601(obj)
    elif type_annotation is timedelta:
        return timedelta_to_iso_8601(obj)
    else:
        raise TypeError(f'Unhandled type {type_annotation}')


def _from_value_to_json(
        value: Any,
        type_annotation: Annotation,
        json_annotation: JSONAnnotation,
        config: SerializerConfig
) -> Any:
    if is_simple_type(type_annotation):
        return _from_simple_to_json(
            value,
            type_annotation
        )
    elif typing_inspect.is_optional_type(type_annotation):
        return _from_optional_obj_to_json(
            value,
            type_annotation,
            json_annotation,
            config
        )
    elif typing_inspect.is_list(type_annotation):
        return _from_list_to_json(
            value,
            type_annotation,
            config
        )
    elif typing_inspect.is_typed_dict(type_annotation):
        return _from_typed_dict_to_json(
            value,
            type_annotation,
            config
        )
    elif typing_inspect.is_union_type(type_annotation):
        return _from_union_obj_to_json(
            value,
            type_annotation,
            json_annotation,
            config
        )
    else:
        raise TypeError


def serialize(
        obj: Any,
        annotation: Annotation,
        config: SerializerConfig
) -> str:
    """Serialize an object to JSON

    Args:
        obj (Any): The object to serialize
        annotation (Annotation): The objects type annotation

    Raises:
        TypeError: If the object cannot be serialized

    Returns:
        str: The JSON string
    """
    type_annotation, json_annotation = get_json_annotation(annotation)
    if not isinstance(json_annotation, JSONValue):
        raise TypeError(
            "Expected the root value to have an JSONValue annotation")

    json_obj = _from_value_to_json(
        obj, type_annotation, json_annotation, config)
    return json.dumps(json_obj)
