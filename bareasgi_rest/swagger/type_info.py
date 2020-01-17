"""Type Info"""

from typing import (
    Any,
    Dict,
    Optional
)

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