"""Utility functions"""

from inspect import Parameter
from typing import Optional

from docstring_parser import Docstring, DocstringParam


def _check_is_required(param: Parameter) -> bool:
    return param.default is Parameter.empty

def _find_docstring_param(
        name: str,
        docstring: Docstring
) -> Optional[DocstringParam]:
    for param in docstring.params:
        if param.arg_name == name:
            return param
    return None
