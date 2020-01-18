"""Swagger errors"""

from typing import Any, Dict, List

from docstring_parser import DocstringRaises


def gather_error_responses(docstring_raises: List[DocstringRaises]) -> Dict[int, Any]:
    """Gather error responses

    Looks for exceptions of type `HTTPError` with a description starting with
    the error code: e.g. `"404, when a book is not found"`

    Args:
        docstring_raises (List[DocstringRaises]): The raises from the docstring

    Returns:
        Dict[int, Any]: The error response schema.
    """
    responses: Dict[int, Any] = {}
    for raises in docstring_raises:
        if raises.type_name != 'HTTPError':
            continue
        first, sep, rest = raises.description.partition(',')
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
