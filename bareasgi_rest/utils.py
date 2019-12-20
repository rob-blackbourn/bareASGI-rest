"""Utility functions"""

from datetime import datetime
from decimal import Decimal
from inspect import Parameter, Signature
import json
from typing import (
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Tuple,
    TypeVar
)
import pytypes

T = TypeVar('T')

class NullIter(Generic[T]):
    """An iterator containing no items"""

    def __aiter__(self):
        return self

    async def __anext__(self) -> T:
        raise StopAsyncIteration


def _is_supported_optional(annotation) -> bool:
    return (
        pytypes.is_subtype(annotation, Optional[str]) or
        pytypes.is_subtype(annotation, Optional[int]) or
        pytypes.is_subtype(annotation, Optional[float]) or
        pytypes.is_subtype(annotation, Optional[Decimal]) or
        pytypes.is_subtype(annotation, Optional[datetime])
    )

def _coerce(value: str, annotation: Any) -> Any:
    if type(annotation) is type:
        single_value = value[0] if isinstance(value, list) else value
        if annotation is str:
            return single_value
        elif annotation is int:
            return int(single_value)
        elif annotation is float:
            return float(single_value)
        elif annotation is Decimal:
            return Decimal(single_value)
        elif annotation is datetime:
            return datetime.fromisoformat(single_value[:-1])
        else:
            raise TypeError
    if pytypes.is_subtype(annotation, Optional[str]):
        return None if not value else _coerce(value, str)
    elif pytypes.is_subtype(annotation, Optional[int]):
        return None if not value else _coerce(value, int)
    elif pytypes.is_subtype(annotation, Optional[float]):
        return None if not value else _coerce(value, float)
    elif pytypes.is_subtype(annotation, Optional[Decimal]):
        return None if not value else _coerce(value, Decimal)
    elif pytypes.is_subtype(annotation, Optional[datetime]):
        return None if not value else _coerce(value, datetime)
    elif pytypes.is_subtype(annotation, List[str]):
        contained_type: Any = str
    elif pytypes.is_subtype(annotation, List[int]):
        contained_type = int
    elif pytypes.is_subtype(annotation, List[float]):
        contained_type = float
    elif pytypes.is_subtype(annotation, List[Decimal]):
        contained_type = Decimal
    elif pytypes.is_subtype(annotation, List[datetime]):
        contained_type = datetime
    else:
        raise TypeError
    return [_coerce(item, contained_type) for item in value]


def make_args(
        sig: Signature,
        matches: Dict[str, str],
        query: Dict[str, Any],
        body: Dict[str, Any]
) -> Tuple[Tuple[Any, ...], Dict[str, Any]]:
    """Make args and kwargs for the given signature from the route matches,
    query args and body.

    :param sig: The function signature
    :type sig: Signature
    :param matches: The route matches
    :type matches: Dict[str, str]
    :param query: A dictionary built from the query string
    :type query: Dict[str, Any]
    :param body: A dictionary build from the body
    :type body: Dict[str, Any]
    :raises KeyError: If a parameter was not found
    :return: A tuple for *args and **kwargs
    :rtype: Tuple[Tuple[Any, ...], Dict[str, Any]]
    """
    kwargs: Dict[str, Any] = {}
    args: List[Any] = []

    for param in sig.parameters.values():
        if param.name in matches:
            value = _coerce(matches[param.name], param.annotation)
        elif param.name in query:
            value = _coerce(query[param.name], param.annotation)
        elif param.name in body:
            value = _coerce(body[param.name], param.annotation)
        elif _is_supported_optional(param.annotation):
            continue
        else:
            raise KeyError

        if param.kind == Parameter.POSITIONAL_ONLY or param.kind == Parameter.POSITIONAL_OR_KEYWORD:
            args.append(value)
        else:
            kwargs[param.name] = value

    bound_args = sig.bind(*args, **kwargs)
    bound_args.apply_defaults()

    return bound_args.args, bound_args.kwargs

def as_datetime(dct):
    for k, v in dct.items():
        try:
            dt = datetime.fromisoformat(v[:-1])
            dct[k] = dt
        except: # pylint: disable=bare-except
            pass
    return dct

class JSONEncoderEx(json.JSONEncoder):
    def default(self, obj):  # pylint: disable=method-hidden,arguments-differ
        if isinstance(obj, datetime):
            return obj.isoformat() + ('Z' if not obj.tzinfo else '')
        elif isinstance(obj, Decimal):
            # return float(str(obj.quantize(Decimal(1)) if obj == obj.to_integral() else obj.normalize()))
            # return {'type{decimal}': str(obj)}
            return float(str(obj.quantize(Decimal(1)) if obj == obj.to_integral() else obj.normalize()))
        else:
            return super(JSONEncoderEx, self).default(obj)
    
