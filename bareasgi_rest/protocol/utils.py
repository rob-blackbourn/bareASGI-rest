"""Protocol utilities"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from ..types import Annotation


from ..typing_inspect import (
    get_optional,
    is_optional_type,
    is_dict,
    is_list,
    is_typed_dict
)


def is_simple_type(annoation: Annotation) -> bool:
    """Return True if the annotation is a simple type like an int or a str.

    Args:
        annoation (Any): The annotation

    Returns:
        bool: True if the annotation is a JSON literal, otherwise False
    """
    return annoation in (
        str,
        bool,
        int,
        float,
        Decimal,
        datetime,
        timedelta
    )


def is_container_type(annotation: Any) -> bool:
    """Return True if this is a JSON container.

    A JSON container can be an object (Like a Dict[str, Any]), or a List.

    Args:
        annotation (Any): The type annotation.

    Returns:
        bool: True if the annotation is represented in JSON as a container.
    """
    if is_optional_type(annotation):
        return is_container_type(get_optional(annotation))
    else:
        return (
            is_list(annotation) or
            is_dict(annotation) or
            is_typed_dict(annotation)
        )
