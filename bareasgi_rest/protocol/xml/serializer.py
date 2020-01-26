"""An XML serializer"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Optional, Type, Union

from lxml import etree
from lxml.etree import Element, SubElement  # pylint: disable=no-name-in-module

import bareasgi_rest.typing_inspect as typing_inspect
from ...types import Annotation
from ..config import SerializerConfig
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
        type_annotation: Type
) -> str:
    if type_annotation is str:
        return obj
    elif type_annotation is int:
        return str(obj)
    elif type_annotation is bool:
        return 'true' if obj else 'false'
    elif type_annotation is float:
        return str(obj)
    elif type_annotation is Decimal:
        return str(obj)
    elif type_annotation is datetime:
        return datetime_to_iso_8601(obj)
    elif type_annotation is timedelta:
        return timedelta_to_iso_8601(obj)
    else:
        raise TypeError(f'Unhandled type {type_annotation}')


def _from_optional(
        obj: Any,
        type_annotation: Annotation,
        xml_annotation: XMLAnnotation,
        element: Optional[Element],
        config: SerializerConfig
) -> Element:
    if obj is None:
        return

    # An optional is a union where the last element is the None type.
    union_types = typing_inspect.get_args(type_annotation)[:-1]
    if len(union_types) == 1:
        # This was Optional[T]
        return _from_obj(
            obj,
            union_types[0],
            xml_annotation,
            element,
            config
        )
    else:
        return _from_union(
            obj,
            Union[tuple(union_types)],
            xml_annotation,
            element,
            config
        )


def _from_union(
        obj: Any,
        type_annotation: Annotation,
        xml_annotation: XMLAnnotation,
        element: Optional[Element],
        config: SerializerConfig
) -> Element:
    for union_type_annotation in typing_inspect.get_args(type_annotation):
        try:
            return _from_obj(
                obj,
                union_type_annotation,
                xml_annotation,
                element,
                config
            )
        except:  # pylint: disable=bare-except
            pass


def _from_list(
        obj: list,
        type_annotation: Annotation,
        xml_annotation: XMLAnnotation,
        element: Optional[Element],
        config: SerializerConfig
) -> Element:
    item_annotation, *_rest = typing_inspect.get_args(type_annotation)
    if typing_inspect.is_annotated_type(item_annotation):
        item_type_annotation, item_xml_annotation = get_xml_annotation(
            item_annotation
        )
    else:
        item_type_annotation = item_annotation
        item_xml_annotation = xml_annotation

    if xml_annotation.tag == item_xml_annotation.tag:
        # siblings
        parent = element
    else:
        parent = _make_element(element, xml_annotation.tag)

    for item in obj:
        _from_obj(
            item,
            item_type_annotation,
            item_xml_annotation,
            parent,
            config
        )

    return parent


def _from_typed_dict(
        obj: dict,
        type_annotation: Annotation,
        xml_annotation: XMLAnnotation,
        element: Optional[Element],
        config: SerializerConfig
) -> Element:
    dict_element = _make_element(element, xml_annotation.tag)

    member_annotations = typing_inspect.typed_dict_annotation(type_annotation)
    for name, member in member_annotations.items():
        if typing_inspect.is_annotated_type(member.annotation):
            item_type_annotation, item_xml_annotation = get_xml_annotation(
                member.annotation
            )
        else:
            tag = config.deserialize_key(member.name)
            item_type_annotation = member.annotation
            item_xml_annotation = XMLEntity(tag)

        _from_obj(
            obj.get(name),
            item_type_annotation,
            item_xml_annotation,
            dict_element,
            config
        )
    return dict_element


def _from_simple(
        obj: Any,
        type_annotation: Annotation,
        xml_annotation: XMLAnnotation,
        element: Optional[Element]
) -> Element:
    text = _simple_type_to_text(obj, type_annotation)
    if isinstance(xml_annotation, XMLAttribute):
        if element is None:
            raise ValueError("No element for attribute")
        element.set(xml_annotation.tag, text)
        return element
    else:
        child = _make_element(element, xml_annotation.tag)
        child.text = text
        return child


def _from_obj(
        obj: Any,
        type_annotation: Annotation,
        xml_annotation: XMLAnnotation,
        element: Optional[Element],
        config: SerializerConfig
) -> Element:
    if is_simple_type(type_annotation):
        return _from_simple(
            obj,
            type_annotation,
            xml_annotation,
            element
        )
    elif typing_inspect.is_optional_type(type_annotation):
        return _from_optional(
            obj,
            type_annotation,
            xml_annotation,
            element,
            config
        )
    elif typing_inspect.is_list(type_annotation):
        return _from_list(
            obj,
            type_annotation,
            xml_annotation,
            element,
            config
        )
    elif typing_inspect.is_typed_dict(type_annotation):
        return _from_typed_dict(
            obj,
            type_annotation,
            xml_annotation,
            element,
            config
        )
    elif typing_inspect.is_union_type(type_annotation):
        return _from_union(
            obj,
            type_annotation,
            xml_annotation,
            element,
            config
        )
    else:
        raise TypeError


def serialize(
        obj: Any,
        annotation: Annotation,
        config: SerializerConfig
) -> str:
    type_annotation, xml_annotation = get_xml_annotation(annotation)
    if not isinstance(xml_annotation, XMLEntity):
        raise TypeError(
            "Expected the root value to have an XMLEntity annotation")

    element = _from_obj(obj, type_annotation, xml_annotation, None, config)
    return etree.tostring(element)  # pylint: disable=c-extension-no-member
