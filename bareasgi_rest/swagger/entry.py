"""Utility functions"""

import inspect
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Sequence
)

from bareasgi.basic_router.path_definition import PathDefinition
import docstring_parser

from ..types import RestCallback

from .config import SwaggerConfig
from .parameters import make_swagger_parameters
from .responses import make_swagger_responses


def make_swagger_entry(
        method: str,
        path_definition: PathDefinition,
        callback: RestCallback,
        consumes: Sequence[bytes],
        produces: Sequence[bytes],
        collection_format: str,
        tags: Optional[List[str]],
        ok_status_code: int,
        ok_status_description: str,
        config: SwaggerConfig
) -> Dict[str, Any]:
    signature = inspect.signature(callback)
    docstring = docstring_parser.parse(inspect.getdoc(callback))
    params = make_swagger_parameters(
        method,
        consumes,
        path_definition,
        signature.parameters,
        docstring,
        collection_format,
        config
    )

    responses = make_swagger_responses(
        signature.return_annotation,
        docstring.returns if docstring else None,
        docstring.raises if docstring else None,
        ok_status_code,
        ok_status_description,
        collection_format,
        config
    )

    entry = {
        'parameters': params,
        'produces': [content_type.decode() for content_type in produces],
        'consumes': [accept.decode() for accept in consumes],
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
