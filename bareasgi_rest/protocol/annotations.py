"""Serialization annotations"""

from abc import ABCMeta
from typing import List, Tuple

from ..types import Annotation
from ..typing_inspect import (
    is_annotated_type,
    get_annotated_type_metadata,
    get_origin
)


class SerializationAnnotation(metaclass=ABCMeta):
    """The base serialization annotation class"""


def is_any_serialization_annotation(annotation: Annotation) -> bool:
    """Determine if the annotation is of type Annotation[T, SerializationAnnotation]

    Args:
        annotation (Any): The annotation

    Returns:
        bool: True if the annotation is of type
            Annotation[T, SerializationAnnotation], otherwise False
    """
    if not is_annotated_type(annotation):
        return False
    for item in get_annotated_type_metadata(annotation):
        if issubclass(type(item), SerializationAnnotation):
            return True
    return False


def get_all_serialization_annotations(
        annotation: Annotation
) -> Tuple[Annotation, List[SerializationAnnotation]]:
    """Gets the type T of Annotation[T, SerializationAnnotation]

    Args:
        annotation (Any): The annotation

    Returns:
        Tuple[Annotation, List[SerializationAnnotation]]: The type and the
            serialization annotationa
    """
    type_annotation = get_origin(annotation)
    serialization_annotations = [
        serialization_annotation
        for serialization_annotation in get_annotated_type_metadata(annotation)
        if issubclass(type(serialization_annotation), SerializationAnnotation)
    ]
    return type_annotation, serialization_annotations
