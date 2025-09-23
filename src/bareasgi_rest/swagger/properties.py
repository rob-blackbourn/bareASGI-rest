"""Type Info"""

from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
import inspect
from inspect import isclass
from typing import Any, TypedDict, get_args, is_typeddict

import docstring_parser
from docstring_parser import Docstring

from jetblack_serialization.custom_annotations import (
    get_default_annotation,
    is_any_default_annotation
)
from jetblack_serialization import Annotation
from jetblack_serialization import typing_ex
from jetblack_serialization.typing_ex import TypedDictFieldInfo

from .config import SwaggerConfig
from .types import SwaggerProperty
from .utils import find_docstring_param


def get_property(
        annotation: Any,
        name: str | None,
        description: str | None,
        default: Any,
        collection_format: str,
        config: SwaggerConfig
) -> SwaggerProperty:
    """Get a swagger property

    Args:
        annotation (Any): The type annotation
        name (str | None): An optional property name
        description (str | None): An optional property description
        default (Any): An optional default where inspect.Parameter.empty indicates no default
        collection_format (str): The swagger collection format

    Raises:
        TypeError: If the property type is not handled.

    Returns:
        dict[str, Any]: The swagger property.
    """
    if typing_ex.is_annotated(annotation):
        return get_property(
            typing_ex.get_annotated_type(annotation),
            name,
            description,
            default,
            collection_format,
            config
        )

    if typing_ex.is_optional(annotation):
        optional_types = typing_ex.get_optional_types(annotation)
        return get_property(
            optional_types[0],
            name,
            description,
            default,
            collection_format,
            config
        )

    if annotation is str:
        prop: SwaggerProperty = {'type': 'string'}
    elif annotation is bool:
        prop = {'type': 'boolean'}
    elif annotation is int:
        prop = {'type': 'integer'}
    elif annotation is float:
        prop = {'type': 'number'}
    elif annotation is Decimal:
        prop = {'type': 'number'}
    elif annotation is datetime:
        prop = {
            'type': 'string',
            'format': 'date-time'
        }
    elif annotation is timedelta:
        # Note: Swagger has no support for durations. I made up the format.
        prop = {
            'type': 'string',
            'format': 'duration'
        }
    elif isclass(annotation) and issubclass(annotation, Enum):
        prop = {
            'type': 'string',
            'enum': list(annotation.__members__.keys())
        }
    elif typing_ex.is_list(annotation):
        contained_type, *_rest = get_args(annotation)
        prop = {
            'type': 'array',
            'collectionFormat': collection_format,
            'items': get_property(
                contained_type,
                None,
                None,
                default,
                collection_format,
                config
            )
        }
    elif is_typeddict(annotation):
        prop = {
            'type': 'object',
            'properties': get_properties(
                annotation,
                docstring_parser.parse(inspect.getdoc(annotation) or ''),
                collection_format,
                config
            )
        }
    elif typing_ex.is_dict(annotation):
        prop = {'type': 'object'}
    else:
        raise TypeError('Unhandled type annotation')

    if name:
        prop['name'] = name

    if description:
        prop['description'] = description

    if default != inspect.Parameter.empty:
        prop['default'] = default

    return prop


def _get_default(
        annotation: object,
        member_annotation: Annotation,
        name: str
) -> Any:
    if is_any_default_annotation(member_annotation):
        _, default_value = get_default_annotation(member_annotation)
        return default_value.value

    return getattr(annotation, name, inspect.Parameter.empty)


def get_properties(
        annotation: type,
        docstring: Docstring,
        collection_format: str,
        config: SwaggerConfig
) -> dict[str, SwaggerProperty]:
    """Get the properties of a TypedDict

    Args:
        annotations (Dict[str, Annotation]): The member
            annotations
        docstring (Docstring): The docstring
        collection_format (str): The collection format

    Returns:
        dict[str, Any]: The swagger properties.
    """
    annotations = typing_ex.typeddict_keys(annotation)
    properties: dict[str, Any] = {}
    for name, info in annotations.items():
        camelcase_name = config.serialize_key(name)
        docstring_param = find_docstring_param(name, docstring)
        description = docstring_param.description if docstring_param else None
        default = _get_default(annotation, info.annotation, name)

        properties[camelcase_name] = get_property(
            info.annotation,
            camelcase_name,
            description,
            default,
            collection_format,
            config
        )

    return properties
