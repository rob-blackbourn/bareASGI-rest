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
import jetblack_serialization.typing_inspect_ex as typing_inspect
from jetblack_serialization.annotations import (
    is_any_serialization_annotation
)

from .config import SwaggerConfig
from .properties import get_property
from .utils import find_docstring_param


def _make_swagger_parameter(
        source: str,
        param: Parameter,
        collection_format: str,
        docstring_param: Optional[DocstringParam],
        config: SwaggerConfig
) -> Dict[str, Any]:
    is_required = param.default is Parameter.empty

    prop = get_property(
        param.annotation,
        config.serialize_key(param.name),
        docstring_param.description if docstring_param else None,
        param.default,
        collection_format,
        config
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
        collection_format: str,
        config: SwaggerConfig
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
                docstring_param,
                config
            )
        )
    return props


def make_swagger_parameters(
        method: str,
        consumes: List[bytes],
        path_definition: PathDefinition,
        parameters: Mapping[str, Parameter],
        docstring: Docstring,
        collection_format: str,
        config: SwaggerConfig
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
            path_variable = config.deserialize_key(segment.name)
            path_variables.add(path_variable)
            parameter = available_parameters.pop(path_variable)
            docstring_param = find_docstring_param(parameter.name, docstring)
            prop = _make_swagger_parameter(
                'path',
                parameter,
                collection_format,
                docstring_param,
                config
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
                collection_format,
                config
            )
        )
    elif (
            b'application/x-www-form-urlencoded' in consumes or
            b'multipart/form-data' in consumes
    ):
        # Form body parameters
        props.extend(
            _make_swagger_parameters_inline(
                'formData',
                available_parameters,
                path_variables,
                docstring,
                collection_format,
                config
            )
        )
    else:
        # Fall back to b'application/json'.
        for parameter in available_parameters.values():
            docstring_param = find_docstring_param(parameter.name, docstring)
            if is_any_serialization_annotation(parameter.annotation):
                body_type = typing_inspect.get_origin(parameter.annotation)
                schema = get_property(
                    body_type,
                    config.serialize_key(parameter.name),
                    None,
                    Parameter.empty,
                    collection_format,
                    config
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
                        docstring_param,
                        config
                    )
                )

    return props
