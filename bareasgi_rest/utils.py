"""Utility functions"""

from datetime import datetime
from decimal import Decimal
from inspect import Parameter, Signature
import json
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Tuple,
    TypeVar,
    cast
)

from bareasgi.basic_router.path_definition import PathDefinition
from inflection import camelize, underscore
import pytypes

T = TypeVar('T')  # pylint: disable=invalid-name


def _rename_dict(dct: Dict[str, Any], rename: Callable[[str], str]) -> Dict[str, Any]:
    return {
        rename(name): _rename_object(obj, rename)
        for name, obj in dct.items()
    }


def _rename_list(lst: List[Any], rename: Callable[[str], str]) -> List[Any]:
    return [_rename_object(obj, rename) for obj in lst]


def _rename_object(obj: T, rename: Callable[[str], str]) -> T:
    if isinstance(obj, dict):
        return cast(T, _rename_dict(cast(Dict[str, Any], obj), rename))
    elif isinstance(obj, list):
        return cast(T, _rename_list(cast(List[Any], obj), rename))
    else:
        return obj


def _camelize(text: str) -> str:
    return camelize(text, uppercase_first_letter=False)


def camelize_object(obj: T) -> T:
    """Convert any dictionary keys in the object to camelcase

    :param obj: The object
    :type obj: T
    :return: The object with keys converted to camelcase
    :rtype: T
    """
    return _rename_object(obj, _camelize)


def underscore_object(obj: T) -> T:
    """Convert any dictionary keys in the object to underscore

    :param obj: The object
    :type obj: T
    :return: The object with keys converted to underscore
    :rtype: T
    """
    return _rename_object(obj, underscore)


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
    if type(annotation) is type:  # pylint: disable=unidiomatic-typecheck
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
        camelcase_name = camelize(param.name, uppercase_first_letter=False)
        if camelcase_name in matches:
            value = _coerce(matches[camelcase_name], param.annotation)
        elif camelcase_name in query:
            value = _coerce(query[camelcase_name], param.annotation)
        elif camelcase_name in body:
            value = _coerce(body[camelcase_name], param.annotation)
        elif _is_supported_optional(param.annotation):
            continue
        else:
            raise KeyError

        if param.kind == Parameter.POSITIONAL_ONLY or param.kind == Parameter.POSITIONAL_OR_KEYWORD:
            args.append(value)
        else:
            # Use the non-camelcased name
            kwargs[param.name] = value

    bound_args = sig.bind(*args, **kwargs)
    bound_args.apply_defaults()

    return bound_args.args, bound_args.kwargs


def as_datetime(dct):
    """Convert datetime like strings"""
    for key, value in dct.items():
        try:
            timestamp = datetime.fromisoformat(value[:-1])
            dct[key] = timestamp
        except:  # pylint: disable=bare-except
            pass
    return dct


class JSONEncoderEx(json.JSONEncoder):
    """Encode json"""

    def default(self, obj):  # pylint: disable=method-hidden,arguments-differ
        if isinstance(obj, datetime):
            return obj.isoformat() + ('Z' if not obj.tzinfo else '')
        elif isinstance(obj, Decimal):
            return float(
                str(obj.quantize(Decimal(1))
                    if obj == obj.to_integral() else
                    obj.normalize())
            )
        else:
            return super(JSONEncoderEx, self).default(obj)
