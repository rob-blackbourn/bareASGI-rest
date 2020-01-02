"""Utility functions"""

from datetime import datetime
from decimal import Decimal
from inspect import Parameter, Signature
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    cast
)

from inflection import camelize, underscore

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
        annotation is Optional[str] or
        annotation is Optional[int] or
        annotation is Optional[float] or
        annotation is Optional[Decimal] or
        annotation is Optional[datetime]
    )


def _coerce_builtin(value: Any, builtin_type: Type) -> Any:
    if isinstance(value, builtin_type):
        return value
    elif isinstance(value, str):
        if builtin_type is str:
            return value
        elif builtin_type is int:
            return int(value)
        elif builtin_type is float:
            return float(value)
        elif builtin_type is Decimal:
            return Decimal(value)
        elif builtin_type is datetime:
            return datetime.fromisoformat(value[:-1])
        else:
            raise TypeError(f'Unhandled type {builtin_type}')
    else:
        raise RuntimeError(f'Unable to coerce value {value}')


def _coerce(value: Any, annotation: Any) -> Any:
    if type(annotation) is type:  # pylint: disable=unidiomatic-typecheck
        single_value = value[0] if isinstance(value, list) else value
        return _coerce_builtin(single_value, annotation)

    if annotation is Optional[str]:
        return None if not value else _coerce(value, str)
    elif annotation is Optional[int]:
        return None if not value else _coerce(value, int)
    elif annotation is Optional[float]:
        return None if not value else _coerce(value, float)
    elif annotation is Optional[Decimal]:
        return None if not value else _coerce(value, Decimal)
    elif annotation is Optional[datetime]:
        return None if not value else _coerce(value, datetime)
    elif annotation is List[str]:
        contained_type: Any = str
    elif annotation is List[int]:
        contained_type = int
    elif annotation is List[float]:
        contained_type = float
    elif annotation is List[Decimal]:
        contained_type = Decimal
    elif annotation is List[datetime]:
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
        name = camelize(param.name, uppercase_first_letter=False)
        if name in matches:
            value = _coerce(matches[name], param.annotation)
        elif name in query:
            value = _coerce(query[name], param.annotation)
        elif name in body:
            value = _coerce(body[name], param.annotation)
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
