"""Utility functions"""

from cgi import parse_multipart
from datetime import datetime
from decimal import Decimal
import io
from inspect import Parameter, Signature
import json
import re
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
from urllib.parse import parse_qs

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


DATETIME_ZULU_REGEX = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$')


def as_datetime(dct):
    """Convert datetime like strings"""
    for key, value in dct.items():
        if isinstance(value, str) and DATETIME_ZULU_REGEX.match(value):
            dct[key] = datetime.fromisoformat(value[:-1])
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

def to_json(obj: Any) -> str:
    """Convert the object to JSON

    Args:
        obj (Any): The object to convert

    Returns:
        str: The stringified object
    """
    return json.dumps(obj, cls=JSONEncoderEx)


def from_json(text: str, _media_type: bytes, _params: Dict[bytes, bytes]) -> Any:
    """Convert JSON to an object

    Args:
        text (str): The JSON string
        _media_type (bytes): The media type
        _params (Dict[bytes, bytes]): The params from content-type header

    Returns:
        Any: The deserialized object.
    """
    return json.loads(text, object_hook=as_datetime)


def from_query_string(
        text: str,
        _media_type: bytes,
        _params: Dict[bytes, bytes]
) -> Any:
    """Convert a query string to a dict

    Args:
        text (str): The query string
        _media_type (bytes): The media type from the content-type header.
        _params (Dict[bytes, bytes]): The params from the content-type header

    Returns:
        Any: The query string as a dict
    """
    return parse_qs(text)


def from_form_data(
        text: str,
        _media_type: bytes,
        params: Dict[bytes, bytes]
) -> Any:
    """Convert form data to a dict

    Args:
        text (str): The form data
        _media_type (bytes): The media type from the content-type header
        params (Dict[bytes, bytes]): The params from the content-type header.

    Raises:
        RuntimeError: If 'boundary' was not in the params

    Returns:
        Any: The form data as a dict.
    """
    if b'boundary' not in params:
        raise RuntimeError('Required "boundary" parameter missing')
    pdict = {
        name.decode(): value
        for name, value in params.items()
    }
    return parse_multipart(io.StringIO(text), pdict)
