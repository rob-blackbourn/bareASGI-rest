"""Utility functions"""

import inspect
from inspect import Signature
from typing import (
    Any,
    Dict,
    List,
    Optional
)

import docstring_parser
from docstring_parser import DocstringReturns, DocstringRaises

import bareasgi_rest.typing_inspect as typing_inspect

from .errors import gather_error_responses
from .type_definitions import TYPE_DEFINITIONS
from .type_info import _add_type_info, _typeddict_schema
from .utils import is_json_container


def _make_json_container_schema(
        annotation: Any,
        collection_format: str
) -> Optional[Dict[str, Any]]:
    if typing_inspect.is_typed_dict(annotation):
        dict_docstring = docstring_parser.parse(
            inspect.getdoc(annotation)
        )
        return _typeddict_schema(
            'object',
            typing_inspect.typed_dict_annotation(annotation),
            dict_docstring,
            collection_format
        )

    if typing_inspect.is_list(annotation):
        nested_type, *_rest = typing_inspect.get_args(annotation)
        if typing_inspect.is_typed_dict(nested_type):
            return _typeddict_schema(
                'array',
                typing_inspect.typed_dict_annotation(nested_type),
                docstring_parser.parse(inspect.getdoc(nested_type)),
                collection_format
            )
        elif typing_inspect.is_dict(nested_type):
            # TODO: What to do for a Dict?
            return None
        else:
            # TODO: What to do for a JSON literal?
            return None

    if typing_inspect.is_dict(annotation):
        # A Dict
        return None

    raise RuntimeError("Not a JSON container")


def make_swagger_response_schema(
        annotation: Any,
        docstring_returns: Optional[DocstringReturns],
        collection_format: str
) -> Optional[Dict[str, Any]]:
    """Make the swagger response schama"""
    if annotation is None:
        return None

    if is_json_container(annotation):
        return _make_json_container_schema(
            annotation,
            collection_format
        )
    else:
        # Something else
        type_def = TYPE_DEFINITIONS.get(annotation)
        if type_def:
            return_type = _add_type_info(
                {},
                annotation,
                collection_format,
                docstring_returns
            )

            return return_type

        return None


def make_swagger_responses(
        return_annotation: Any,
        docstring_returns: Optional[DocstringReturns],
        docstring_raises: Optional[List[DocstringRaises]],
        ok_status_code: int,
        ok_status_description: str,
        collection_format: str
) -> Dict[int, Dict[str, Any]]:
    ok_response: Dict[str, Any] = {
        'description': ok_status_description
    }

    ok_response_schema = make_swagger_response_schema(
        return_annotation,
        docstring_returns,
        collection_format
    )
    if ok_response_schema is not None:
        ok_response['schema'] = ok_response_schema

    responses: Dict[int, Dict[str, Any]] = {
        ok_status_code: ok_response
    }
    if docstring_raises:
        error_responses = gather_error_responses(docstring_raises)
        responses.update(error_responses)

    return responses
