"""Type Info"""

from datetime import datetime
from decimal import Decimal
import inspect
from typing import (
    Any,
    Dict,
    Optional
)

import docstring_parser
from docstring_parser import Docstring, DocstringMeta
from inflection import camelize

import bareasgi_rest.typing_inspect as typing_inspect

from .type_definitions import TYPE_DEFINITIONS
from .utils import _find_docstring_param


def _add_type_info(
        prop: Dict[str, Any],
        annotation: Any,
        collection_format: str,
        docstring_meta: Optional[DocstringMeta]
) -> Dict[str, Any]:
    if typing_inspect.is_typed_dict(annotation):
        dict_props = _typeddict_schema(
            'object',
            typing_inspect.typed_dict_annotation(annotation),
            None,
            'multi'
        )
        prop.update(dict_props)
        return prop

    type_def = TYPE_DEFINITIONS[annotation]
    if type_def['is_list']:
        prop['type'] = 'array'
        prop['collectionFormat'] = collection_format
        items = {
            'type': type_def['type']
        }
        if type_def['format'] is not None:
            items['format'] = type_def['format']
        prop['items'] = items
    else:
        prop['type'] = type_def['type']
        if type_def['format'] is not None:
            prop['format'] = type_def['format']

    if docstring_meta is not None and docstring_meta.description:
        prop['description'] = docstring_meta.description

    return prop


def _typeddict_schema(
        schema_type: str,
        annotations: Dict[str, typing_inspect.TypedDictMember],
        docstring: Optional[Docstring],
        collection_format: str
) -> Dict[str, Any]:
    properties: Dict[str, Any] = {}
    for name, annotation in annotations.items():
        prop = _add_type_info(
            {},
            annotation.annotation,
            collection_format,
            _find_docstring_param(name, docstring) if docstring else None
        )

        camelcase_name = camelize(name, False)
        prop['name'] = camelcase_name
        properties[camelcase_name] = prop

    if schema_type == 'object':
        return {
            'type': 'object',
            'properties': properties
        }
    else:
        return {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': properties
            }
        }


def get_property(
        annotation: Any,
        name: Optional[str],
        description: Optional[str],
        default: Any,
        collection_format: str
) -> Dict[str, Any]:
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
    elif annotation is int:
        prop['type'] = 'integer'
    elif annotation is float:
        prop['type'] = 'number'
    elif annotation is Decimal:
        prop['type'] = 'number'
    elif annotation is datetime:
        prop['type'] = 'string'
        prop['format'] = 'date-time'
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
        raise RuntimeError('Invalid JSON literal')

    return prop


def get_properties(
        annotations: Dict[str, typing_inspect.TypedDictMember],
        docstring: Docstring,
        collection_format: str
) -> Dict[str, Any]:
    properties: Dict[str, Any] = {}
    for name, member in annotations.items():
        camelcase_name = camelize(name, False)
        docstring_param = _find_docstring_param(name, docstring)
        description = docstring_param.description if docstring_param else None

        properties[camelcase_name] = get_property(
            member.annotation,
            camelcase_name,
            description,
            member.default,
            collection_format
        )

    return properties
