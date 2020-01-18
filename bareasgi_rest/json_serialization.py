"""Serialization"""

from cgi import parse_multipart
from datetime import datetime
from decimal import Decimal
import io
import json
import re
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Pattern,
    Tuple,
    Type,
    TypeVar,
    cast
)
from urllib.parse import parse_qs

from inflection import camelize, underscore

import bareasgi_rest.typing_inspect as typing_inspect

DATETIME_ZULU_REGEX = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$')

DateTimeFormat = Tuple[str, Pattern, Optional[Callable[[str], str]]]

DATETIME_FORMATS: Tuple[DateTimeFormat, ...] = (
    (
        "%Y-%m-%dT%H:%M:%SZ",
        re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$'),
        None
    ),
    (
        "%Y-%m-%dT%H:%M:%S.%fZ",
        re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z$'),
        None
    ),
    (
        "%Y-%m-%dT%H:%M:%S%z",
        re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$'),
        lambda s: s[0:-3] + s[-2:]
    ),
    (
        "%Y-%m-%dT%H:%M:%S.%f%z",
        re.compile(
            r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+[+-]\d{2}:\d{2}$'),
        lambda s: s[0:-3] + s[-2:]
    )
)


def json_to_datetime(value: str) -> Optional[datetime]:
    """Parse a JSON date

    Args:
        value (str): The JSON date string

    Returns:
        Optional[datetime]: A timestamp
    """
    if isinstance(value, str):
        for fmt, pattern, transform in DATETIME_FORMATS:
            if pattern.match(value):
                text = transform(value) if transform else value
                return datetime.strptime(text, fmt)
    return None


def as_datetime(dct):
    """Convert datetime like strings"""
    for key, value in dct.items():
        if isinstance(value, str):
            timestamp = json_to_datetime(value)
            if timestamp:
                dct[key] = timestamp
    return dct


def datetime_to_json(timestamp: datetime) -> str:
    """Convert datetime to JSON

    Args:
        timestamp (datetime): The timestamp

    Returns:
        str: The stringified JSON version of the timestamp
    """
    date_part = "{year:04d}-{month:02d}-{day:02d}".format(
        year=timestamp.year, month=timestamp.month, day=timestamp.day,
    )
    time_part = "{hour:02d}:{minute:02d}:{second:02d}.{millis:02d}".format(
        hour=timestamp.hour, minute=timestamp.minute, second=timestamp.second,
        millis=timestamp.microsecond // 1000
    )

    utcoffset = timestamp.utcoffset()
    if utcoffset is None:
        return f"{date_part}T{time_part}Z"
    else:
        tz_seconds = utcoffset.total_seconds()
        tz_sign = '-' if tz_seconds < 0 else '+'
        tz_minutes = int(abs(tz_seconds)) // 60
        tz_hours = tz_minutes // 60
        tz_minutes %= 60
        return f"{date_part}T{time_part}{tz_sign}{tz_hours:02d}:{tz_minutes:02d}"


class JSONEncoderEx(json.JSONEncoder):
    """Encode json"""

    def default(self, obj):  # pylint: disable=method-hidden,arguments-differ
        if isinstance(obj, datetime):
            return datetime_to_json(obj)
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


def is_json_literal(annoation: Any) -> bool:
    """Return True if the annotation is a JSON literal

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
        datetime
    )


def _from_json_value_to_builtin(value: Any, builtin_type: Type) -> Any:
    if isinstance(value, builtin_type):
        return value
    elif isinstance(value, str):
        if builtin_type is str:
            return value
        elif builtin_type is int:
            return int(value)
        elif builtin_type is bool:
            return value.lower() == 'true'
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


def from_json_value(value: Any, annotation: Any) -> Any:
    if is_json_literal(annotation):
        single_value = value[0] if isinstance(value, list) else value
        return _from_json_value_to_builtin(single_value, annotation)

    if typing_inspect.is_optional_type(annotation):
        optional_type = typing_inspect.get_optional(annotation)
        return None if not value else from_json_value(value, optional_type)
    elif typing_inspect.is_list(annotation):
        element_type, *_rest = typing_inspect.get_args(annotation)
        return [from_json_value(item, element_type) for item in value]
    elif typing_inspect.is_dict(annotation):
        return underscore_object(value)
    elif typing_inspect.is_typed_dict(annotation):
        return _from_json_value_to_typed_dict(value, annotation)
    else:
        raise TypeError


def _from_json_value_to_typed_dict(
        values: Optional[Dict[str, Any]],
        annotation: Any
) -> Optional[Dict[str, Any]]:
    if values is None or not typing_inspect.is_typed_dict(annotation):
        return values

    coerced_values: Dict[str, Any] = {}

    member_annotations = typing_inspect.typed_dict_annotation(annotation)
    for name, member in member_annotations.items():
        camelcase_name = camelize(name, False)
        if camelcase_name in values:
            if typing_inspect.is_typed_dict(member.annotation):
                coerced_values[name] = _from_json_value_to_typed_dict(
                    values[camelcase_name],
                    member.annotation
                )
            else:
                coerced_values[name] = from_json_value(
                    values[camelcase_name],
                    member.annotation
                )
        elif member.default is typing_inspect.TypedDictMember.empty:
            raise KeyError(
                f'Required key "{camelcase_name}" is missing'
            )
        else:
            coerced_values[name] = from_json_value(
                member.default, member.annotation)

    return coerced_values
