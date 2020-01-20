"""Serialization"""

from cgi import parse_multipart
from datetime import datetime, timedelta
from decimal import Decimal
import io
import json
from typing import Any, Callable, Dict

from urllib.parse import parse_qs

from ..iso_8601 import (
    iso_8601_to_datetime,
    datetime_to_iso_8601,
    iso_8601_to_timedelta,
    timedelta_to_iso_8601
)
from .coercion import from_json_value


def json_to_python(dct):
    """Convert JSON recognized objects to Python.

    This includes durations and dates.

    Args:
        dct ([type]): The source dictionary

    Returns:
        [type]: The dictionary with conversions.
    """
    for key, value in dct.items():
        if isinstance(value, str):
            timestamp = iso_8601_to_datetime(value)
            if timestamp:
                dct[key] = timestamp
                continue
            duration = iso_8601_to_timedelta(value)
            if duration:
                dct[key] = duration
                continue
    return dct


class JSONEncoderEx(json.JSONEncoder):
    """Encode json"""

    def default(self, obj):  # pylint: disable=method-hidden,arguments-differ
        if isinstance(obj, datetime):
            return datetime_to_iso_8601(obj)
        elif isinstance(obj, timedelta):
            return timedelta_to_iso_8601(obj)
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


def from_json(
        text: str,
        _media_type: bytes,
        _params: Dict[bytes, bytes],
        annotation: Any,
        rename_external: Callable[[str], str],
) -> Any:
    """Convert JSON to an object

    Args:
        text (str): The JSON string
        _media_type (bytes): The media type
        _params (Dict[bytes, bytes]): The params from content-type header
        annotation (str): The type annotation
        rename (Callable[[str], str]): A function to rename object keys.

    Returns:
        Any: The deserialized object.
    """
    obj = json.loads(text)
    return from_json_value(obj, annotation, rename_external)


def from_query_string(
        text: str,
        _media_type: bytes,
        _params: Dict[bytes, bytes],
        annotation: Any,
        rename_external: Callable[[str], str],
) -> Any:
    """Convert a query string to a dict

    Args:
        text (str): The query string
        _media_type (bytes): The media type from the content-type header.
        _params (Dict[bytes, bytes]): The params from the content-type header
        _annotation (str): The type annotation
        rename (Callable[[str], str]): A function to rename object keys.

    Returns:
        Any: The query string as a dict
    """
    return parse_qs(text)


def from_form_data(
        text: str,
        _media_type: bytes,
        params: Dict[bytes, bytes],
        annotation: Any,
        rename_external: Callable[[str], str],
) -> Any:
    """Convert form data to a dict

    Args:
        text (str): The form data
        _media_type (bytes): The media type from the content-type header
        params (Dict[bytes, bytes]): The params from the content-type header.
        _annotation(str): The type annotation
        rename (Callable[[str], str]): A function to rename object keys.

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
