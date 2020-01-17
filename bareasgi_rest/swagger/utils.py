"""Utility functions"""

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

def is_json_container(annotation: Any) -> bool:
    """Return True if this is a JSON container.

    A JSON container can be an object (Like a Dict[str, Any]), or a List.
    
    Args:
        annotation (Any): The type annotation.
    
    Returns:
        bool: True if the annotation is represented in JSON as a container.
    """
    if typing_inspect.is_optional_type(annotation):
        return is_json_container(typing_inspect.get_optional(annotation))
    else:
        return (
            typing_inspect.is_list(annotation) or
            typing_inspect.is_dict(annotation) or
            typing_inspect.is_typed_dict(annotation)
        )
