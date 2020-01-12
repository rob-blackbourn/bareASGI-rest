"""Typing inspect extensions"""

import inspect
from typing import Any, Dict, Tuple, NamedTuple
from typing_inspect import * # pylint: disable=unused-wildcard-import
try:
    # For 3.8
    from typing import TypedDict, _TypedDictMeta
    def is_typed_dict(annotation) -> bool:
        return isinstance(annotation, _TypedDictMeta)
except ImportError:
    # For 3.7
    from typing_extensions import TypedDict, _TypedDictMeta
    def is_typed_dict(annotation) -> bool:
        return isinstance(annotation, _TypedDictMeta)

class _empty:
    """Marker object for Signature.empty and Parameter.empty."""

class TypedDictMember(NamedTuple):
    name: str
    annotation: Any
    default: Any = _empty

    empty = _empty

def typed_dict_annotation(td: Any) -> Dict[str, TypedDictMember]:
    return {
        name: TypedDictMember(
            name,
            value,
            getattr(td, name, TypedDictMember.empty)
        )
        for name, value in td.__annotations__.items()
    } if is_typed_dict(td) else None
