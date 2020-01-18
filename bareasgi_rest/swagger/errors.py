"""Swagger errors"""

from typing import Any, Dict, List

from docstring_parser import DocstringRaises


def gather_error_responses(docstring_raises: List[DocstringRaises]) -> Dict[int, Any]:
    """Gather error responses"""
    responses: Dict[int, Any] = {}
    for raises in docstring_raises:
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
