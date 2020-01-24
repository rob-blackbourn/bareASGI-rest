"""XML Serialization"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Type,
    Union
)

from lxml import etree
from lxml.etree import Element  # pylint: disable=no-name-in-module

import bareasgi_rest.typing_inspect as typing_inspect
from ..iso_8601 import (
    iso_8601_to_datetime,
    iso_8601_to_timedelta
)
from ...types import Annotation
from ..utils import is_simple_type

from .annotations import (
    XMLAnnotation,
    XMLAttribute,
    XMLEntity,
    get_xml_annotation
)


def _is_element_empty(element: Element, xml_annotation: XMLAnnotation) -> bool:
    if isinstance(xml_annotation, XMLAttribute):
        return xml_annotation.tag not in element.attrib
    else:
        return (
            element.find('*') is None and
            element.text is None and
            not element.attrib
        )


def _from_xml_element_to_builtin(text: str, builtin_type: Type) -> Any:
    if builtin_type is str:
        return text
    elif builtin_type is int:
        return int(text)
    elif builtin_type is bool:
        return text.lower() == 'true'
    elif builtin_type is float:
        return float(text)
    elif builtin_type is Decimal:
        return Decimal(text)
    elif builtin_type is datetime:
        timestamp = iso_8601_to_datetime(text)
        if timestamp is None:
            raise ValueError(f"Unable co convert '{text}' to datetime")
        return timestamp
    elif builtin_type is timedelta:
        duration = iso_8601_to_timedelta(text)
        if duration is None:
            raise ValueError(f"Unable co convert '{text}' to timedelta")
        return duration
    else:
        raise TypeError(f'Unhandled type {builtin_type}')


def _from_xml_element_to_union(
        element: Element,
        annotation: Annotation,
        xml_annotation: XMLAnnotation
) -> Any:
    for element_type in typing_inspect.get_args(annotation):
        try:
            return _from_xml_element(
                element,
                element_type,
                xml_annotation
            )
        except:  # pylint: disable=bare-except
            pass


def _from_xml_to_optional_type(
        element: Element,
        element_type: Annotation,
        xml_annotation: XMLAnnotation
) -> Any:
    if _is_element_empty(element, xml_annotation):
        return None

    # An optional is a union where the last element is the None type.
    union_types = typing_inspect.get_args(element_type)[:-1]
    if len(union_types) == 1:
        # This was Optional[T]
        return _from_xml_element(element, union_types[0], xml_annotation)
    else:
        return _from_xml_element_to_union(
            element,
            Union[tuple(union_types)],
            xml_annotation
        )


def _from_xml_to_simple_type(
        element: Element,
        element_type: Annotation,
        xml_annotation: XMLAnnotation
) -> Any:
    if not isinstance(xml_annotation, XMLAttribute):
        text = element.text
    else:
        text = element.attrib[xml_annotation.tag]
    if text is None:
        raise ValueError(f'Expected "{xml_annotation.tag}" to be non-null')
    return _from_xml_element_to_builtin(text, element_type)


def _from_xml_element_to_list(
        element: Element,
        annotation: Annotation,
        xml_annotation: XMLAnnotation
) -> List[Any]:
    element_annotation, *_rest = typing_inspect.get_args(annotation)
    element_type, element_xml_annotation = get_xml_annotation(
        element_annotation
    )

    if xml_annotation.tag == element_xml_annotation.tag:
        # siblings
        elements: Iterable[Element] = element.iterfind(
            '../' + element_xml_annotation.tag)
    else:
        # nested
        elements = element.iter(element_xml_annotation.tag)

    return [
        _from_xml_element(
            child,
            element_type,
            element_xml_annotation
        )
        for child in elements
    ]


def _from_xml_element_to_typed_dict(
        element: Optional[Element],
        annotation: Annotation,
) -> Optional[Dict[str, Any]]:
    if element is None:
        return None

    coerced_values: Dict[str, Any] = {}

    member_annotations = typing_inspect.typed_dict_annotation(annotation)
    for name, member in member_annotations.items():
        element_type, xml_annotation = get_xml_annotation(member.annotation)
        if not isinstance(xml_annotation, XMLAttribute):
            member_element = element.find('./' + xml_annotation.tag)
        else:
            member_element = element
        if member_element is not None:
            coerced_values[name] = _from_xml_element(
                member_element,
                element_type,
                xml_annotation
            )
        elif member.default is typing_inspect.TypedDictMember.empty:
            raise KeyError(
                f'Required key "{xml_annotation.tag}" is missing'
            )
        else:
            coerced_values[name] = _from_xml_element(
                member.default,
                element_type,
                xml_annotation
            )

    return coerced_values


def _from_xml_element(
        element: Element,
        element_type: Annotation,
        xml_annotation: XMLAnnotation
) -> Any:

    if is_simple_type(element_type):
        return _from_xml_to_simple_type(element, element_type, xml_annotation)
    if typing_inspect.is_optional_type(element_type):
        return _from_xml_to_optional_type(element, element_type, xml_annotation)
    elif typing_inspect.is_list(element_type):
        return _from_xml_element_to_list(element, element_type, xml_annotation)
    elif typing_inspect.is_typed_dict(element_type):
        return _from_xml_element_to_typed_dict(element, element_type)
    elif typing_inspect.is_union_type(element_type):
        return _from_xml_element_to_union(element, element_type, xml_annotation)
    raise TypeError


def deserialise_xml(
        text: str,
        annotation: Annotation
) -> Any:
    """Convert XML to an object

    Args:
        text (str): The XML string
        annotation (str): The type annotation

    Returns:
        Any: The deserialized object.
    """
    element_type, xml_annotation = get_xml_annotation(annotation)
    if not isinstance(xml_annotation, XMLEntity):
        raise TypeError(
            "Expected the root value to have an XMLEntity annotation")

    element = etree.fromstring(text)  # pylint: disable=c-extension-no-member
    return _from_xml_element(element, element_type, xml_annotation)
