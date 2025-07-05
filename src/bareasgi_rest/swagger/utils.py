"""Swagger Utility functions"""

from docstring_parser import Docstring, DocstringParam


def find_docstring_param(
        name: str,
        docstring: Docstring
) -> DocstringParam | None:
    """Find the docstring param for the given parameter name.

    Args:
        name (str): The parameter name
        docstring (Docstring): The docstring

    Returns:
        DocstringParam | None: The docstring param or None if not found.
    """
    for param in docstring.params:
        if param.arg_name == name:
            return param
    return None
