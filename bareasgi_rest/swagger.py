"""Utility functions"""

from datetime import datetime
from decimal import Decimal
import inspect
from inspect import Parameter, Signature
from typing import (
    AbstractSet,
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    cast
)

from bareasgi.basic_router.path_definition import PathDefinition
import docstring_parser
from docstring_parser import Docstring, DocstringParam, DocstringMeta
from inflection import underscore, camelize

import bareasgi_rest.typing_inspect as typing_inspect


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
        'format': 'date-time',
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
        'format': 'date-time',
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
        'format': 'date-time',
    }
}


def _check_is_required(param: Parameter) -> bool:
    return param.default is Parameter.empty

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

def _make_swagger_parameter(
        source: str,
        param: Parameter,
        collection_format: str,
        docstring_param: Optional[DocstringParam]
) -> Dict[str, Any]:
    is_required = _check_is_required(param)

    parameter = {
        'name': camelize(param.name, False)
    }

    _add_type_info(
        parameter,
        param.annotation,
        collection_format,
        docstring_param
    )

    if source != 'body':
        parameter['in'] = source
        parameter['required'] = is_required

    if param.default != Parameter.empty:
        parameter['default'] = param.default

    return parameter

def _make_swagger_schema(
        params: List[Tuple[str, Parameter, DocstringParam]],
        collection_format: str
) -> Dict[str, Any]:
    return {
        'type': 'object',
        'required': [
            name
            for name, param, docstring_param in params
            if _check_is_required(param)
        ],
        'properties': {
            name: _make_swagger_parameter(
                'body',
                param,
                collection_format,
                docstring_param
            )
            for name, param, docstring_param in params
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


def make_swagger_path(path_definition: PathDefinition) -> str:
    """Make a path compatible with swagger"""
    swagger_path = '/' + '/'.join(
        '{' + segment.name + '}' if segment.is_variable else segment.name
        for segment in path_definition.segments
    )
    if path_definition.ends_with_slash:
        swagger_path += '/'
    return swagger_path


def make_swagger_parameters(
        method: str,
        accept: bytes,
        path_definition: PathDefinition,
        signature: Signature,
        docstring: Docstring,
        collection_format: str
) -> List[Dict[str, Any]]:
    """Make the swagger parameters"""

    # Path parameters
    parameters: List[Dict[str, Any]] = []
    path_variables: Set[str] = set()
    for segment in path_definition.segments:
        if segment.is_variable:
            path_variable = underscore(segment.name)
            path_variables.add(path_variable)
            param = signature.parameters[path_variable]
            docstring_param = _find_docstring_param(param.name, docstring)
            parameter = _make_swagger_parameter(
                'path',
                param,
                collection_format,
                docstring_param
            )
            parameters.append(parameter)

    if method == 'GET':
        # Query parameters
        parameters.extend(
            _make_swagger_parameters_inline(
                'query',
                signature,
                path_variables,
                docstring,
                collection_format
            )
        )
    elif accept in (b'application/x-www-form-urlencoded', b'multipart/form-data'):
        # Form body parameters
        parameters.extend(
            _make_swagger_parameters_inline(
                'formData',
                signature,
                path_variables,
                docstring,
                collection_format
            )
        )
    else:
        # Fall back to b'application/json'.
        params = [
            (
                camelize(param.name, False),
                param,
                _find_docstring_param(param.name, docstring)
            )
            for param in signature.parameters.values()
            if param.name not in path_variables
        ]
        if len(params) == 1 and typing_inspect.is_typed_dict(params[0][1].annotation):
            _name, param, _docstring = params[0]
            param_docstring = inspect.getdoc(param.annotation)
            schema = _typeddict_schema(
                'object',
                typing_inspect.typed_dict_annotation(param.annotation),
                docstring_parser.parse(param_docstring),
                collection_format
            )
        else:
            schema = _make_swagger_schema(params, collection_format)
        parameters.append({
            'in': 'body',
            'name': 'schema',
            'description': 'The body schema',
            'schema': schema
        })

    return parameters


def make_swagger_response_schema(
        signature: Signature,
        docstring: Optional[Docstring],
        collection_format: str
) -> Optional[Dict[str, Any]]:
    """Make the swagger response schama"""
    if signature.return_annotation is None:
        return None

    if typing_inspect.is_typed_dict(signature.return_annotation):
        dict_docstring = docstring_parser.parse(
            inspect.getdoc(signature.return_annotation)
        )
        return _typeddict_schema(
            'object',
            typing_inspect.typed_dict_annotation(signature.return_annotation),
            dict_docstring,
            collection_format
        )
    elif typing_inspect.is_list(signature.return_annotation):
        args = typing_inspect.get_args(signature.return_annotation)
        if len(args) != 1:
            return None
        nested_type = args[0]
        if not typing_inspect.is_typed_dict(nested_type):
            return None
        return _typeddict_schema(
            'array',
            typing_inspect.typed_dict_annotation(nested_type),
            docstring_parser.parse(inspect.getdoc(nested_type)),
            collection_format
        )
    elif typing_inspect.is_dict(signature.return_annotation):
        # A Dict
        return None
    else:
        # Something else
        type_def = TYPE_DEFINITIONS.get(signature.return_annotation)
        if type_def:
            return_type = _add_type_info(
                {},
                signature.return_annotation,
                collection_format,
                docstring.returns if docstring else None
            )

            return return_type

        return None


def gather_error_responses(docstring: Docstring) -> Dict[int, Any]:
    """Gather error responses"""
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
        except:  # pylint: disable=bare-except
            continue
    return responses

def make_swagger_responses(
        signature: Signature,
        docstring: Optional[Docstring],
        ok_status_code: int,
        ok_status_description: str,
        collection_format: str
) -> Dict[int, Dict[str, Any]]:
    ok_response: Dict[str, Any] = {
        'description': ok_status_description
    }

    ok_response_schema = make_swagger_response_schema(
        signature,
        docstring,
        collection_format
    )
    if ok_response_schema is not None:
        ok_response['schema'] = ok_response_schema

    responses: Dict[int, Dict[str, Any]] = {
        ok_status_code: ok_response
    }
    if docstring:
        error_responses = gather_error_responses(docstring)
        responses.update(error_responses)

    return responses

def make_swagger_entry(
        method: str,
        path_definition: PathDefinition,
        callback: Callable[..., Awaitable[Any]],
        accept: bytes,
        content_type: bytes,
        collection_format: str,
        tags: Optional[List[str]],
        status_code: int,
        status_description: str
) -> Dict[str, Any]:
    signature = inspect.signature(callback)
    docstring = docstring_parser.parse(inspect.getdoc(callback))
    params = make_swagger_parameters(
        method,
        accept,
        path_definition,
        signature,
        docstring,
        collection_format
    )

    responses = make_swagger_responses(
        signature,
        docstring,
        status_code,
        status_description,
        collection_format
    )

    entry = {
        'parameters': params,
        'produces': [content_type.decode()],
        'consumes': [accept.decode()],
        'responses': responses
    }

    if docstring:
        if docstring.short_description:
            entry['summary'] = docstring.short_description
        if docstring.long_description:
            entry['description'] = docstring.long_description

    if tags:
        entry['tags'] = tags

    return entry
