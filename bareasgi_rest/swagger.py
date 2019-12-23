"""Utility functions"""

from datetime import datetime
from decimal import Decimal
from inspect import Parameter, Signature
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple
)

from bareasgi.basic_router.path_definition import PathDefinition
from docstring_parser.parser import Docstring
from docstring_parser.parser.common import DocstringParam


def make_swagger_path(path_definition: PathDefinition) -> str:
    swagger_path = '/' + '/'.join(
        '{' + segment.name + '}' if segment.is_variable else segment.name
        for segment in path_definition.segments
    )
    if path_definition.ends_with_slash:
        swagger_path += '/'
    return swagger_path


TYPE_DEFINITIONS = {
    str: {
        'is_required': True,
        'is_list': False,
        'type': 'string',
        'format': None,
    },
    int: {
        'is_required': True,
        'is_list': False,
        'type': 'integer',
        'format': None,
    },
    float: {
        'is_required': True,
        'type': 'number',
        'format': None,
    },
    Decimal: {
        'is_required': True,
        'is_list': False,
        'type': 'number',
        'format': None,
    },
    datetime: {
        'is_required': True,
        'is_list': False,
        'type': 'string',
        'format': 'date',
    },
    Optional[str]: {
        'is_required': False,
        'is_list': False,
        'type': 'string',
        'format': None,
    },
    Optional[int]: {
        'is_required': False,
        'is_list': False,
        'type': 'integer',
        'format': None,
    },
    Optional[float]: {
        'is_required': False,
        'is_list': False,
        'type': 'number',
        'format': None,
    },
    Optional[Decimal]: {
        'is_required': False,
        'is_list': False,
        'type': 'number',
        'format': None,
    },
    Optional[datetime]: {
        'is_required': False,
        'is_list': False,
        'type': 'string',
        'format': 'date',
    },
    List[str]: {
        'is_required': False,
        'is_list': True,
        'type': 'string',
        'format': None,
    },
    List[int]: {
        'is_required': False,
        'is_list': True,
        'type': 'integer',
        'format': None,
    },
    List[float]: {
        'is_required': False,
        'is_list': True,
        'type': 'string',
        'format': None,
    },
    List[Decimal]: {
        'is_required': False,
        'is_list': True,
        'type': 'number',
        'format': None,
    },
    List[datetime]: {
        'is_required': False,
        'is_list': True,
        'type': 'string',
        'format': 'date',
    }
}


def _make_swagger_parameter(
        source: str,
        param: Parameter,
        collection_format: str,
        docstring_param: Optional[DocstringParam]
) -> Dict[str, Any]:
    type_def = TYPE_DEFINITIONS[param.annotation]
    parameter = {
        'name': param.name,
        'type': 'array' if type_def['is_list'] else type_def['type']
    }

    if type_def['format'] is not None:
        parameter['format'] = type_def['format']

    if type_def['is_list']:
        parameter['collectionFormat'] = collection_format
        items = {
            'type': type_def['type']
        }
        if type_def['format'] is not None:
            items['format'] = type_def['format']
        parameter['items'] = items

    if source != 'body':
        parameter['in'] = source
        parameter['required'] = type_def['is_required']

    if param.default != Parameter.empty:
        parameter['default'] = param.default

    if docstring_param is not None and docstring_param.description:
        parameter['description'] = docstring_param.description
    return parameter


def _make_swagger_schema(
        params: List[Tuple[Parameter, DocstringParam]],
        collection_format: str
) -> Dict[str, Any]:
    return {
        'type': 'object',
        'required': [
            param.name
            for param, _ in params
            if TYPE_DEFINITIONS[param.annotation]['is_required']
        ],
        'properties': {
            param.name: _make_swagger_parameter(
                'body',
                param,
                collection_format,
                docstring_param
            )
            for param, docstring_param in params
        }
    }


def _find_docstring_param(
        name: str,
        docstring: Docstring
) -> Optional[DocstringParam]:
    for param in docstring.params:
        if param.arg_name == name:
            return param
    return None


def make_swagger_parameters(
        method: str,
        accept: bytes,
        path_definition: PathDefinition,
        sig: Signature,
        docstring: Docstring,
        collection_format: str
) -> List[Dict[str, Any]]:
    parameters: List[Dict[str, Any]] = []
    for segment in path_definition.segments:
        if segment.is_variable:
            param = sig.parameters[segment.name]
            argdoc = _find_docstring_param(param.name, docstring)
            parameter = _make_swagger_parameter(
                'path',
                param,
                collection_format,
                argdoc
            )
            parameters.append(parameter)

    if method == 'GET':
        source = 'query'
    elif accept in (b'application/x-www-form-urlencoded', b'multipart/form-data'):
        source = 'formData'
    else:
        source = 'body'

    for param in sig.parameters.values():
        if param.name in path_definition.segments:
            continue
        argdoc = _find_docstring_param(param.name, docstring)
        parameter = _make_swagger_parameter(
            source,
            param,
            collection_format,
            argdoc
        )
        parameters.append(parameter)

    return parameters
