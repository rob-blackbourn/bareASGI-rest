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
from stringcase import camelcase

import bareasgi_rest.typing_inspect as typing_inspect

from .utils import find_docstring_param


def get_property(
        annotation: Any,
        name: Optional[str],
        description: Optional[str],
        default: Any,
        collection_format: str
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
            collection_format
        )

    if typing_inspect.is_optional_type(annotation):
        optional_type = typing_inspect.get_optional(annotation)
        return get_property(
            optional_type,
            name,
            description,
            default,
            collection_format
        )

    prop: Dict[str, Any] = {}

    if name:
        prop['name'] = name

    if description:
        prop['description'] = description

    if default != typing_inspect.TypedDictMember.empty:
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
    elif typing_inspect.is_list(annotation):
        contained_type, *_rest = typing_inspect.get_args(annotation)
        prop['type'] = 'array'
        prop['collectionFormat'] = collection_format
        prop['items'] = get_property(
            contained_type,
            None,
            None,
            default,
            collection_format
        )
    elif typing_inspect.is_dict(annotation):
        prop['type'] = 'object'
    elif typing_inspect.is_typed_dict(annotation):
        prop['type'] = 'object'
        prop['properties'] = get_properties(
            typing_inspect.typed_dict_annotation(annotation),
            docstring_parser.parse(inspect.getdoc(annotation)),
            collection_format
        )
    else:
        raise TypeError('Unhandled type annotation')

    return prop


def get_properties(
        annotations: Dict[str, typing_inspect.TypedDictMember],
        docstring: Docstring,
        collection_format: str
) -> Dict[str, Any]:
    """Get the properties of a TypedDict

    Args:
        annotations (Dict[str, typing_inspect.TypedDictMember]): The member
            annotations
        docstring (Docstring): The docstring
        collection_format (str): The collection format

    Returns:
        Dict[str, Any]: The swagger properties.
    """
    properties: Dict[str, Any] = {}
    for name, member in annotations.items():
        camelcase_name = camelcase(name)
        docstring_param = find_docstring_param(name, docstring)
        description = docstring_param.description if docstring_param else None

        properties[camelcase_name] = get_property(
            member.annotation,
            camelcase_name,
            description,
            member.default,
            collection_format
        )

    return properties
