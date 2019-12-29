"""Utility functions"""

from datetime import datetime
from decimal import Decimal
import inspect
from inspect import Parameter, Signature
from typing import (
    AbstractSet,
    Any,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    cast
)

from bareasgi.basic_router.path_definition import PathDefinition
import docstring_parser
from docstring_parser import Docstring, DocstringParam
from inflection import underscore, camelize
import typing_inspect


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
        'name': camelize(param.name, False),
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
        path_variables: AbstractSet[str],
        docstring: Docstring,
        collection_format: str
) -> List[Dict[str, Any]]:
    """Make inline paramters for query or form"""
    parameters: List[Dict[str, Any]] = []
    for param in sig.parameters.values():
        if param.name in path_variables:
            continue
        docstring_param = _find_docstring_param(param.name, docstring)
        parameter = _make_swagger_parameter(
            source,
            param,
            collection_format,
            docstring_param
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
    path_variables: Set[str] = set()
    for segment in path_definition.segments:
        if segment.is_variable:
            path_variable = underscore(segment.name)
            path_variables.add(path_variable)
            param = sig.parameters[path_variable]
            docstring_param = _find_docstring_param(param.name, docstring)
            parameter = _make_swagger_parameter(
                'path',
                param,
                collection_format,
                docstring_param
            )
            parameters.append(parameter)

    if method == 'GET':
        parameters.extend(
            _make_swagger_parameters_inline(
                'query',
                sig,
                path_variables,
                docstring,
                collection_format
            )
        )
    elif accept in (b'application/x-www-form-urlencoded', b'multipart/form-data'):
        parameters.extend(
            _make_swagger_parameters_inline(
                'formData',
                sig,
                path_variables,
                docstring,
                collection_format
            )
        )
    else:
        params = [
            (param, _find_docstring_param(param.name, docstring))
            for param in sig.parameters.values()
            if param.name not in path_variables
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


def gather_error_responses(docstring: Docstring) -> Dict[int, Any]:
    responses: Dict[int, Any] = {}
    for raises in docstring.raises:
        if raises.type_name != 'HTTPError':
            continue
        first, sep, rest = raises.description.partition(',')
        if not sep:
            continue
        try:
            error_code = int(first.strip())
            responses[error_code] = {
                'description': rest.strip()
            }
        except:
            continue
    return responses


def _typeddict_schema(
    schema_type: str,
    annotations: Dict[str, Any],
    docstring: Optional[Docstring]
) -> Dict[str, Any]:
    properties: Dict[str, Any] = {}
    for name, value in annotations.items():
        prop: Dict[str, Any] = {}
        docstring_param = _find_docstring_param(name, docstring)
        if docstring_param is not None:
            prop['description'] = docstring_param.description
        type_def = TYPE_DEFINITIONS.get(value)
        if type_def is not None:
            prop['type'] = type_def['type']
            if type_def['format'] is not None:
                prop['format'] = type_def['format']
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


def make_swagger_response_schema(
        sig: Signature
) -> Optional[Dict[str, Any]]:
    if sig.return_annotation is None:
        return None

    origin = typing_inspect.get_origin(sig.return_annotation)
    if not origin and issubclass(sig.return_annotation, dict):
        # could be a typed dict
        annotations = getattr(sig.return_annotation, '__annotations__', None)
        if isinstance(annotations, dict):
            docstring = docstring_parser.parse(
                inspect.getdoc(sig.return_annotation)
            )
            return _typeddict_schema('object', annotations, docstring)
        else:
            return None
    elif origin and origin is list:
        # could be a list of typed dicts
        args = typing_inspect.get_args(sig.return_annotation)
        if len(args) != 1:
            return None
        nested_type = args[0]
        nested_origin = typing_inspect.get_origin(nested_type)
        if nested_origin and nested_origin is dict:
            # List[Dict]
            return None
        elif not nested_origin and issubclass(nested_type, dict):
            # A TypedDict
            annotations = getattr(nested_type, '__annotations__', None)
            if isinstance(annotations, dict):
                # List[TypedDict]
                docstring = docstring_parser.parse(inspect.getdoc(nested_type))
                return _typeddict_schema('array', annotations, docstring)
            else:
                # List[Dict]
                return None
        else:
            # List
            return None
    elif origin and origin is dict:
        # A Dict
        return None

    # Something else
    return None
