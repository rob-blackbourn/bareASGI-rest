"""Utility functions"""

from typing import (
    Any,
    Dict,
    List,
    Optional
)

from docstring_parser import DocstringReturns, DocstringRaises

import bareasgi_rest.typing_inspect as typing_inspect

from .errors import gather_error_responses
from .type_info import get_property


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

    if return_annotation is not None:
        ok_response['schema'] = get_property(
            return_annotation,
            None,
            docstring_returns.description if docstring_returns else None,
            typing_inspect.TypedDictMember.empty,
            collection_format
        )

    responses: Dict[int, Dict[str, Any]] = {
        ok_status_code: ok_response
    }
    if docstring_raises:
        error_responses = gather_error_responses(docstring_raises)
        responses.update(error_responses)

    return responses
