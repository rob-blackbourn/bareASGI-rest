"""Parameters"""

from inspect import Parameter
from typing import (
    AbstractSet,
    Any,
    Dict,
    List,
    Mapping,
    Optional,
    Set,
    Tuple
)

from bareasgi.basic_router.path_definition import PathDefinition
from docstring_parser import Docstring, DocstringParam
from inflection import camelize, underscore

import bareasgi_rest.typing_inspect as typing_inspect

from .type_info import get_property
from .utils import _check_is_required, _find_docstring_param


def _make_swagger_parameter(
        source: str,
        param: Parameter,
        collection_format: str,
        docstring_param: Optional[DocstringParam]
) -> Dict[str, Any]:
    is_required = _check_is_required(param)

    prop = get_property(
        param.annotation,
        camelize(param.name, False),
        docstring_param.description if docstring_param else None,
        param.default,
        collection_format
    )

    if source != 'body':
        prop['in'] = source
        prop['required'] = is_required

    return prop


def _make_swagger_parameters_inline(
        source: str,
        parameters: Mapping[str, Parameter],
        path_variables: AbstractSet[str],
        docstring: Docstring,
        collection_format: str
) -> List[Dict[str, Any]]:
    """Make inline paramters for query or form"""
    props: List[Dict[str, Any]] = []
    for param in parameters.values():
        if param.name in path_variables:
            continue
        docstring_param = _find_docstring_param(param.name, docstring)
        prop = _make_swagger_parameter(
            source,
            param,
            collection_format,
            docstring_param
        )
        props.append(prop)
    return props


def _make_swagger_schema(
        params: List[Tuple[str, Parameter, DocstringParam]],
        collection_format: str
) -> Dict[str, Any]:
    return {
        'type': 'object',
        'required': [
            name
            for name, param, docstring_param in params
            if param.default is Parameter.empty
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


def make_swagger_parameters(
        method: str,
        accept: bytes,
        path_definition: PathDefinition,
        parameters: Mapping[str, Parameter],
        docstring: Docstring,
        collection_format: str
) -> List[Dict[str, Any]]:
    """Make the swagger parameters"""

    # Path parameters
    props: List[Dict[str, Any]] = []
    path_variables: Set[str] = set()
    for segment in path_definition.segments:
        if segment.is_variable:
            path_variable = underscore(segment.name)
            path_variables.add(path_variable)
            param = parameters[path_variable]
            docstring_param = _find_docstring_param(param.name, docstring)
            prop = _make_swagger_parameter(
                'path',
                param,
                collection_format,
                docstring_param
            )
            props.append(prop)

    if method == 'GET':
        # Query parameters
        props.extend(
            _make_swagger_parameters_inline(
                'query',
                parameters,
                path_variables,
                docstring,
                collection_format
            )
        )
    elif accept in (b'application/x-www-form-urlencoded', b'multipart/form-data'):
        # Form body parameters
        props.extend(
            _make_swagger_parameters_inline(
                'formData',
                parameters,
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
            for param in parameters.values()
            if param.name not in path_variables
        ]
        if len(params) == 1 and typing_inspect.is_typed_dict(params[0][1].annotation):
            _name, param, _docstring = params[0]
            schema = get_property(
                param.annotation,
                camelize(param.name, False),
                None,
                Parameter.empty,
                collection_format
            )
        else:
            schema = _make_swagger_schema(params, collection_format)
        props.append({
            'in': 'body',
            'name': 'schema',
            'description': 'The body schema',
            'schema': schema
        })

    return props
