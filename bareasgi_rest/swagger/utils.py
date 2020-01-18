"""Utility functions"""

from datetime import datetime
from decimal import Decimal
from inspect import Parameter
from typing import Any, Optional

from docstring_parser import Docstring, DocstringParam

import bareasgi_rest.typing_inspect as typing_inspect


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
