"""Type Info"""

from datetime import datetime, timedelta
from decimal import Decimal
import inspect
from typing import (
    Any,
    Dict,
    Optional
)

import docstring_parser
from docstring_parser import Docstring

from jetblack_serialization.types import Annotation
import jetblack_serialization.typing_inspect_ex as typing_inspect

from .config import SwaggerConfig
from .utils import find_docstring_param


def get_property(
        annotation: Any,
        name: Optional[str],
        description: Optional[str],
        default: Any,
        collection_format: str,
        config: SwaggerConfig
) -> Dict[str, Any]:
    """Get a swagger property

    Args:
        annotation (Any): The type annotation
        name (Optional[str]): An optional property name
        description (Optional[str]): An optional property description
        default (Any): An optional default where inspect.Parameter.empty indicates no default
        collection_format (str): The swagger collection format

    Raises:
        TypeError: If the property type is not handled.

    Returns:
        Dict[str, Any]: The swagger property.
    """
    if typing_inspect.is_annotated_type(annotation):
        return get_property(
            typing_inspect.get_origin(annotation),
            name,
            description,
            default,
            collection_format,
            config
        )

    if typing_inspect.is_optional_type(annotation):
        optional_type = typing_inspect.get_optional_type(annotation)
        return get_property(
            optional_type,
            name,
            description,
            default,
            collection_format,
            config
        )

    prop: Dict[str, Any] = {}

    if name:
        prop['name'] = name

    if description:
        prop['description'] = description

    if default != inspect.Parameter.empty:
        prop['default'] = default

    if annotation is str:
        prop['type'] = 'string'
    elif annotation is bool:
        prop['type'] = 'boolean'
    elif annotation is int:
        prop['type'] = 'integer'
    elif annotation is float:
        prop['type'] = 'number'
    elif annotation is Decimal:
        prop['type'] = 'number'
    elif annotation is datetime:
        prop['type'] = 'string'
        prop['format'] = 'date-time'
    elif annotation is timedelta:
        # Note: Swagger has no support for durations. I made up the format.
        prop['type'] = 'string'
        prop['format'] = 'duration'
    elif typing_inspect.is_list_type(annotation):
        contained_type, *_rest = typing_inspect.get_args(annotation)
        prop['type'] = 'array'
        prop['collectionFormat'] = collection_format
        prop['items'] = get_property(
            contained_type,
            None,
            None,
            default,
            collection_format,
            config
        )
    elif typing_inspect.is_dict_type(annotation):
        prop['type'] = 'object'
    elif typing_inspect.is_typed_dict_type(annotation):
        prop['type'] = 'object'
        prop['properties'] = get_properties(
            annotation,
            docstring_parser.parse(inspect.getdoc(annotation)),
            collection_format,
            config
        )
    else:
        raise TypeError('Unhandled type annotation')

    return prop


def get_properties(
        annotation,
        docstring: Docstring,
        collection_format: str,
        config: SwaggerConfig
) -> Dict[str, Any]:
    """Get the properties of a TypedDict

    Args:
        annotations (Dict[str, Annotation]): The member
            annotations
        docstring (Docstring): The docstring
        collection_format (str): The collection format

    Returns:
        Dict[str, Any]: The swagger properties.
    """
    annotations: Dict[str, Annotation] = typing_inspect.typed_dict_keys(
        annotation
    )
    properties: Dict[str, Any] = {}
    for name, member_annotation in annotations.items():
        camelcase_name = config.serialize_key(name)
        docstring_param = find_docstring_param(name, docstring)
        description = docstring_param.description if docstring_param else None
        default = getattr(annotation, name, inspect.Parameter.empty)

        properties[camelcase_name] = get_property(
            member_annotation,
            camelcase_name,
            description,
            default,
            collection_format,
            config
        )

    return properties
