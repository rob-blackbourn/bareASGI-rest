"""Serialization"""

from cgi import parse_multipart
from datetime import datetime
from decimal import Decimal
import io
import json
import re
from typing import (
    Any,
    Dict
)
from urllib.parse import parse_qs

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
