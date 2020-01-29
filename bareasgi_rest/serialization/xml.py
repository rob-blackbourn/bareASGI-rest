"""Helpers"""

from typing import Any

from jetblack_serialization.config import SerializerConfig
from jetblack_serialization.types import Annotation
from jetblack_serialization.xml.deserializer import deserialize
from jetblack_serialization.xml.serializer import serialize

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
