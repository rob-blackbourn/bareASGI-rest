"""Utility functions"""

import inspect
from inspect import Signature
from typing import (
    Any,
    Dict,
    Optional
)

import docstring_parser
from docstring_parser import Docstring

import bareasgi_rest.typing_inspect as typing_inspect

from .type_definitions import TYPE_DEFINITIONS
from .type_info import _add_type_info, _typeddict_schema


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
