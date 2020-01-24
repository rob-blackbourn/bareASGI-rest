"""XML annotations"""

from abc import ABCMeta
from typing import Tuple

from ...types import Annotation
from ...typing_inspect import (
    is_annotated_type,
    get_annotated_type_metadata,
    get_origin
)


class JSONAnnotation(metaclass=ABCMeta):
    """The base JSON annotation class"""


class JSONValue(JSONAnnotation):
    """A JSON property"""

    def __repr__(self) -> str:
        return 'JSONValue()'


class JSONProperty(JSONAnnotation):
    """A JSON property"""

    def __init__(self, tag: str):
        self.tag = tag

    def __repr__(self) -> str:
        return f'JSONProperty(tag="{self.tag}")'


class JSONObject(JSONProperty):
    """A JSON object"""

    def __repr__(self) -> str:
        return f'JSONObject("tag={self.tag}")'


class JSONList(JSONProperty):
    """A JSON list"""

    def __repr__(self) -> str:
        return f'JSONList(tag="{self.tag}")'


def is_json_annotation(annotation: Annotation) -> bool:
    """Determine if the annotation is of type Annotation[T, JSONAnnotation]

    Args:
        annotation (Any): The annotation

    Returns:
        bool: True if the annotation is of type Annotation[T, JSONAnnotation],
            otherwise False
    """
    return (
        is_annotated_type(annotation) and
        issubclass(get_annotated_type_metadata(annotation)[0], JSONAnnotation)
    )


def get_json_annotation(annotation: Annotation) -> Tuple[Annotation, JSONAnnotation]:
    """Gets the type T of Annotation[T, JSONAnnotation]

    Args:
        annotation (Any): The annotation

    Returns:
        Tuple[Annotation, JSONAnnotation]: The type and the JSON annotation
    """
    return get_origin(annotation), get_annotated_type_metadata(annotation)[0]
