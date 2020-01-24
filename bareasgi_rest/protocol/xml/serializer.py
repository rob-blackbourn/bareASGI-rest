"""An XML serializer"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Optional, Type, Union

from lxml import etree
from lxml.etree import Element, SubElement  # pylint: disable=no-name-in-module

import bareasgi_rest.typing_inspect as typing_inspect
from ...types import Annotation
from ..utils import is_simple_type
from ..iso_8601 import (
    datetime_to_iso_8601,
    timedelta_to_iso_8601
)

from .annotations import (
    XMLAnnotation,
    XMLAttribute,
    XMLEntity,
    get_xml_annotation
)


def _make_element(parent: Optional[Element], tag: str) -> Element:
    return Element(tag) if parent is None else SubElement(parent, tag)


def _simple_type_to_text(
        obj: Any,
        element_type: Type
) -> str:
    if element_type is str:
        return obj
    elif element_type is int:
        return str(obj)
    elif element_type is bool:
        return 'true' if obj else 'false'
    elif element_type is float:
        return str(obj)
    elif element_type is Decimal:
        return str(obj)
    elif element_type is datetime:
        return datetime_to_iso_8601(obj)
    elif element_type is timedelta:
        return timedelta_to_iso_8601(obj)
    else:
        raise TypeError(f'Unhandled type {element_type}')


def _from_optional_obj_to_xml(
        obj: Any,
        element_type: Annotation,
        xml_annotation: XMLAnnotation,
        element: Optional[Element]
) -> Element:
    if obj is None:
        return

    # An optional is a union where the last element is the None type.
    union_types = typing_inspect.get_args(element_type)[:-1]
    if len(union_types) == 1:
        # This was Optional[T]
        return _from_obj_to_xml(
            obj,
            union_types[0],
            xml_annotation,
            element
        )
    else:
        return _from_union_obj_to_xml(
            obj,
            Union[tuple(union_types)],
            xml_annotation,
            element
        )


def _from_union_obj_to_xml(
        obj: Any,
        annotation: Annotation,
        xml_annotation: XMLAnnotation,
        element: Optional[Element]
) -> Element:
    for element_type in typing_inspect.get_args(annotation):
        try:
            return _from_obj_to_xml(
                obj,
                element_type,
                xml_annotation,
                element
            )
        except:  # pylint: disable=bare-except
            pass


def _from_list_to_xml(
        obj: list,
        annotation: Annotation,
        xml_annotation: XMLAnnotation,
        element: Optional[Element]
) -> Element:
    element_annotation, *_rest = typing_inspect.get_args(annotation)
    element_type, element_xml_annotation = get_xml_annotation(
        element_annotation
    )

    if xml_annotation.tag == element_xml_annotation.tag:
        # siblings
        parent = element
    else:
        parent = _make_element(element, xml_annotation.tag)

    for item in obj:
        _from_obj_to_xml(
            item,
            element_type,
            element_xml_annotation,
            parent
        )

    return parent


def _from_typed_dict_to_xml(
        obj: dict,
        annotation: Annotation,
        xml_annotation: XMLAnnotation,
        element: Optional[Element]
) -> Element:
    dict_element = _make_element(element, xml_annotation.tag)

    member_annotations = typing_inspect.typed_dict_annotation(annotation)
    for name, member in member_annotations.items():
        member_type, member_xml_annotation = get_xml_annotation(
            member.annotation
        )

        _from_obj_to_xml(
            obj.get(name),
            member_type,
            member_xml_annotation,
            dict_element
        )
    return dict_element


def _from_simple_to_xml(
        obj: Any,
        element_type: Annotation,
        xml_annotation: XMLAnnotation,
        element: Optional[Element]
) -> Element:
    text = _simple_type_to_text(obj, element_type)
    if isinstance(xml_annotation, XMLAttribute):
        if element is None:
            raise ValueError("No element for attribute")
        element.set(xml_annotation.tag, text)
        return element
    else:
        child = _make_element(element, xml_annotation.tag)
        child.text = text
        return child


def _from_obj_to_xml(
        obj: Any,
        element_type: Annotation,
        xml_annotation: XMLAnnotation,
        element: Optional[Element]
) -> Element:
    if is_simple_type(element_type):
        return _from_simple_to_xml(obj, element_type, xml_annotation, element)
    elif typing_inspect.is_optional_type(element_type):
        return _from_optional_obj_to_xml(obj, element_type, xml_annotation, element)
    elif typing_inspect.is_list(element_type):
        return _from_list_to_xml(obj, element_type, xml_annotation, element)
    elif typing_inspect.is_typed_dict(element_type):
        return _from_typed_dict_to_xml(obj, element_type, xml_annotation, element)
    elif typing_inspect.is_union_type(element_type):
        return _from_union_obj_to_xml(obj, element_type, xml_annotation, element)
    else:
        raise TypeError


def serialize(obj: Any, annotation: Annotation) -> str:
    element_type, xml_annotation = get_xml_annotation(annotation)
    if not isinstance(xml_annotation, XMLEntity):
        raise TypeError(
            "Expected the root value to have an XMLEntity annotation")

    element = _from_obj_to_xml(obj, element_type, xml_annotation, None)
    return etree.tostring(element)  # pylint: disable=c-extension-no-member
