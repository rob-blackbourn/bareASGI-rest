"""XML annotations"""

from abc import ABCMeta
from typing import Tuple

from ...types import Annotation
from ...typing_inspect import (
    is_annotated_type,
    get_annotated_type_metadata,
    get_origin
)


class XMLAnnotation(metaclass=ABCMeta):
    """The base XML annotation class"""

    def __init__(self, tag: str):
        self.tag = tag


class XMLEntity(XMLAnnotation):
    """An XML entity"""

    def __repr__(self) -> str:
        return f'XMLEntity("tag={self.tag}")'


class XMLAttribute(XMLAnnotation):
    """An XML attribute"""

    def __repr__(self) -> str:
        return f'XMLAttribute(tag="{self.tag}")'


def is_xml_annotation(annotation: Annotation) -> bool:
    """Determine if the annotation is of type Annotation[T, XMLAnnotation]

    Args:
        annotation (Any): The annotation

    Returns:
        bool: True if the annotation is of type Annotation[T, XMLAnnotation],
            otherwise False
    """
    return (
        is_annotated_type(annotation) and
        issubclass(get_annotated_type_metadata(annotation)[0], XMLAnnotation)
    )


def get_xml_annotation(annotation: Annotation) -> Tuple[Annotation, XMLAnnotation]:
    """Gets the type T of Annotation[T, XMLAnnotation]

    Args:
        annotation (Any): The annotation

    Returns:
        Tuple[Annotation, XMLAnnotation]: The type and the XML annotation
    """
    return get_origin(annotation), get_annotated_type_metadata(annotation)[0]
