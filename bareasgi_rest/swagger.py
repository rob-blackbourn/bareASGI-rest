"""Utility functions"""

from datetime import datetime
from decimal import Decimal
from inspect import Parameter, Signature
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    cast
)

from bareasgi.basic_router.path_definition import PathDefinition
from docstring_parser import Docstring, DocstringParam
from inflection import underscore


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


def _check_is_required(
        param: Parameter,
        docstring_param: DocstringParam
) -> bool:
    type_def = TYPE_DEFINITIONS[param.annotation]
    is_required: bool = cast(bool, type_def['is_required']) or (
        docstring_param is not None and not docstring_param.is_optional
    )
    return is_required


def _make_swagger_parameter(
        source: str,
        param: Parameter,
        collection_format: str,
        docstring_param: Optional[DocstringParam]
) -> Dict[str, Any]:
    type_def = TYPE_DEFINITIONS[param.annotation]
    is_required = _check_is_required(param, docstring_param)

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
        parameter['required'] = is_required

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
            for param, docstring_param in params
            if _check_is_required(param, docstring_param)
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


def _make_swagger_parameters_inline(
        source: str,
        sig: Signature,
        path_definition: PathDefinition,
        docstring: Docstring,
        collection_format: str
) -> List[Dict[str, Any]]:
    """Make inline paramters for query or form"""
    parameters: List[Dict[str, Any]] = []
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
            param = sig.parameters[underscore(segment.name)]
            argdoc = _find_docstring_param(param.name, docstring)
            parameter = _make_swagger_parameter(
                'path',
                param,
                collection_format,
                argdoc
            )
            parameters.append(parameter)

    if method == 'GET':
        parameters.extend(
            _make_swagger_parameters_inline(
                'query',
                sig,
                path_definition,
                docstring,
                collection_format
            )
        )
    elif accept in (b'application/x-www-form-urlencoded', b'multipart/form-data'):
        parameters.extend(
            _make_swagger_parameters_inline(
                'formData',
                sig,
                path_definition,
                docstring,
                collection_format
            )
        )
    else:
        params = [
            (param, _find_docstring_param(param.name, docstring))
            for param in sig.parameters.values()
        ]
        schema = _make_swagger_schema(
            params,
            collection_format
        )
        parameters.append({
            'in': 'body',
            'name': 'schema',
            'description': 'The body schema',
            'schema': schema
        })

    return parameters
