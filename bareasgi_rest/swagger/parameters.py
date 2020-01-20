"""Parameters"""

from inspect import Parameter
from typing import (
    AbstractSet,
    Any,
    Dict,
    List,
    Mapping,
    Optional,
    Set
)

from bareasgi.basic_router.path_definition import PathDefinition
from docstring_parser import Docstring, DocstringParam
from inflection import underscore

from ..utils import (
    is_body_type,
    get_body_type,
    camelcase
)

from .properties import get_property
from .utils import find_docstring_param


def _make_swagger_parameter(
        source: str,
        param: Parameter,
        collection_format: str,
        docstring_param: Optional[DocstringParam]
) -> Dict[str, Any]:
    is_required = param.default is Parameter.empty

    prop = get_property(
        param.annotation,
        camelcase(param.name),
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
    for parameter in parameters.values():
        if parameter.name in path_variables:
            continue
        docstring_param = find_docstring_param(parameter.name, docstring)
        props.append(
            _make_swagger_parameter(
                source,
                parameter,
                collection_format,
                docstring_param
            )
        )
    return props


def make_swagger_parameters(
        method: str,
        accept: bytes,
        path_definition: PathDefinition,
        parameters: Mapping[str, Parameter],
        docstring: Docstring,
        collection_format: str
) -> List[Dict[str, Any]]:
    """Make the swagger parameters"""

    available_parameters = {
        name: parameter
        for name, parameter in parameters.items()
    }

    # Path parameters
    props: List[Dict[str, Any]] = []
    path_variables: Set[str] = set()
    for segment in path_definition.segments:
        if segment.is_variable:
            path_variable = underscore(segment.name)
            path_variables.add(path_variable)
            parameter = available_parameters.pop(path_variable)
            docstring_param = find_docstring_param(parameter.name, docstring)
            prop = _make_swagger_parameter(
                'path',
                parameter,
                collection_format,
                docstring_param
            )
            props.append(prop)

    if method == 'GET':
        # Query parameters
        props.extend(
            _make_swagger_parameters_inline(
                'query',
                available_parameters,
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
                available_parameters,
                path_variables,
                docstring,
                collection_format
            )
        )
    else:
        # Fall back to b'application/json'.
        for parameter in available_parameters.values():
            docstring_param = find_docstring_param(parameter.name, docstring)
            if is_body_type(parameter.annotation):
                body_type = get_body_type(parameter.annotation)
                schema = get_property(
                    body_type,
                    camelcase(parameter.name),
                    None,
                    Parameter.empty,
                    collection_format
                )
                props.append({
                    'in': 'body',
                    'name': 'schema',
                    'description': 'The body schema',
                    'schema': schema
                })
            else:
                props.append(
                    _make_swagger_parameter(
                        'query',
                        parameter,
                        collection_format,
                        docstring_param
                    )
                )

    return props
