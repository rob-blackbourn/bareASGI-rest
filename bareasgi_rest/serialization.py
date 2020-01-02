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
    Optional,
    Tuple
)
from urllib.parse import parse_qs

DATETIME_ZULU_REGEX = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$')

DateTimeFormat = Tuple[str, re.Pattern, Optional[Callable[[str], str]]]

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
        re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+[+-]\d{2}:\d{2}$'),
        lambda s: s[0:-3] + s[-2:]
    )
)


def json_to_datetime(value: str) -> Optional[datetime]:
    if isinstance(value, str):
        for fmt, pattern, transform in DATETIME_FORMATS:
            if pattern.match(value):
                s = transform(value) if transform else value
                return datetime.strptime(s, fmt)
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
    utcoffset = timestamp.utcoffset()
    if utcoffset is None:
        return "{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}.{millis:02d}Z".format(
            year=timestamp.year, month=timestamp.month, day=timestamp.day,
            hour=timestamp.hour, minute=timestamp.minute, second=timestamp.second,
            millis=timestamp.microsecond // 1000
        )
    else:
        tz_seconds = utcoffset.total_seconds()
        tz_sign = '-' if tz_seconds < 0 else '+'
        tz_minutes = int(abs(tz_seconds)) // 60
        tz_hours = tz_minutes // 60
        tz_minutes %= 60
        return "{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}.{millis:02d}{tz_sign}{tz_hours:02d}:{tz_minutes:02d}".format(
            year=timestamp.year, month=timestamp.month, day=timestamp.day,
            hour=timestamp.hour, minute=timestamp.minute, second=timestamp.second,
            millis=timestamp.microsecond // 1000,
            tz_sign=tz_sign, tz_hours=tz_hours, tz_minutes=tz_minutes
        )

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
