"""Helpers"""

from typing import Any

from jetblack_serialization import Annotation, SerializerConfig
from jetblack_serialization.xml import serialize, deserialize

from ..types import (
    MediaType,
    MediaTypeParams
)


def from_xml(
        _media_type: MediaType,
        _params: MediaTypeParams,
        config: SerializerConfig,
        text: str,
        annotation: Annotation
) -> Any:
    return deserialize(text, annotation, config)


def to_xml(
        _media_type: MediaType,
        _params: MediaTypeParams,
        config: SerializerConfig,
        obj: Any,
        annotation: Any,
) -> str:
    return serialize(obj, annotation, config)
