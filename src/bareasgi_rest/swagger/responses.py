"""Utility functions"""

import inspect
from typing import Any

from docstring_parser import DocstringReturns, DocstringRaises

from .config import SwaggerConfig
from .errors import gather_error_responses
from .properties import get_property
from .types import SwaggerResponse


def make_swagger_responses(
        return_annotation: Any,
        docstring_returns: DocstringReturns | None,
        docstring_raises: list[DocstringRaises] | None,
        ok_status_code: int,
        ok_status_description: str,
        collection_format: str,
        config: SwaggerConfig
) -> dict[int, SwaggerResponse]:
    ok_response: SwaggerResponse = {
        'description': ok_status_description
    }

    if return_annotation is not None:
        ok_response['schema'] = get_property(
            return_annotation,
            None,
            docstring_returns.description if docstring_returns else None,
            inspect.Parameter.empty,
            collection_format,
            config
        )

    responses: dict[int, SwaggerResponse] = {
        ok_status_code: ok_response
    }
    if docstring_raises:
        error_responses = gather_error_responses(docstring_raises)
        responses |= error_responses

    return responses
