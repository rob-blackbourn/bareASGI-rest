"""Utility functions"""

import inspect
from typing import (
    Any,
    Dict,
    List,
    Optional,
)

from bareasgi.basic_router.path_definition import PathDefinition
import docstring_parser

from ..types import RestCallback
from .parameters import make_swagger_parameters
from .responses import make_swagger_responses


def make_swagger_entry(
        method: str,
        path_definition: PathDefinition,
        callback: RestCallback,
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
