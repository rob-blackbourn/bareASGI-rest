"""Serialization"""

from cgi import parse_multipart
from functools import partial
import io
from typing import Any, Callable

from urllib.parse import parse_qs

from jetblack_serialization.config import SerializerConfig
from jetblack_serialization.types import Annotation
from jetblack_serialization.json import serialize, deserialize, from_json_value

from ..types import (
    MediaType,
    MediaTypeParams
)


def to_json(
        _media_type: MediaType,
        _params: MediaTypeParams,
        config: SerializerConfig,
        obj: Any,
        annotation: Any,
) -> str:
    """Convert the object to JSON

    Args:
        obj (Any): The object to convert

    Returns:
        str: The stringified object
    """
    return serialize(obj, annotation, config)


def from_json(
        _media_type: MediaType,
        _params: MediaTypeParams,
        config: SerializerConfig,
        text: str,
        annotation: Annotation
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
    return deserialize(text, annotation, config)


def from_query_string(
        _media_type: MediaType,
        _params: MediaTypeParams,
        _config: SerializerConfig,
        text: str,
        _annotation: Annotation
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
        _media_type: MediaType,
        params: MediaTypeParams,
        _config: SerializerConfig,
        text: str,
        _annotation: Annotation
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


def json_arg_deserializer_factory(
        config: SerializerConfig,
) -> Callable[[str, Annotation], Any]:
    return partial(from_json_value, config)
