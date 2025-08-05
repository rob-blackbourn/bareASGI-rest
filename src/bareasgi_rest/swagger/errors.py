"""Swagger errors"""

from docstring_parser import DocstringRaises

from .types import SwaggerResponse


def gather_error_responses(
        docstring_raises: list[DocstringRaises]
) -> dict[int, SwaggerResponse]:
    """Gather error responses

    Looks for exceptions of type `RestError` with a description starting with
    the error code: e.g. `"404, when a book is not found"`

    Args:
        docstring_raises (list[DocstringRaises]): The raises from the docstring

    Returns:
        dict[int, Any]: The error response schema.
    """
    responses: dict[int, SwaggerResponse] = {}
    for raises in docstring_raises:
        if raises.type_name != 'RestError':
            continue
        description = raises.description or ''
        first, sep, rest = description.partition(',')
        if not sep:
            continue
        try:
            error_code = int(first.strip())
            description = rest.strip()
            responses[error_code] = {
                'description': description
            }
        except:  # pylint: disable=bare-except
            continue
    return responses
