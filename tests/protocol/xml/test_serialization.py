"""Round trip tests for XML serialization"""

from datetime import datetime
from typing import List, Optional, Union

from stringcase import capitalcase, snakecase
from typing_extensions import TypedDict, Annotated  # type: ignore

from bareasgi_rest.protocol.config import SerializerConfig
from bareasgi_rest.protocol.xml.serializer import serialize
from bareasgi_rest.protocol.xml.deserializer import deserialize
from bareasgi_rest.protocol.xml.annotations import (
    XMLEntity,
    XMLAttribute
)

CONFIG = SerializerConfig(capitalcase, snakecase)


class AnnotatedBook(TypedDict, total=False):
    book_id: Annotated[int, XMLAttribute("bookId")]
    title: Annotated[str, XMLEntity("Title")]
    author: Annotated[str, XMLEntity("Author")]
    publication_date: Annotated[datetime, XMLEntity("PublicationDate")]
    keywords: Annotated[
        List[Annotated[str, XMLEntity("Keyword")]],
        XMLEntity("Keywords")
    ]
    phrases: Annotated[
        List[Annotated[str, XMLEntity("Phrase")]],
        XMLEntity("Phrase")
    ]
    age: Annotated[Optional[Union[datetime, int]], XMLEntity("Age")]
    pages: Annotated[Optional[int], XMLAttribute("pages")]


def test_typed():
    dct: AnnotatedBook = {
        'author': 'Chairman Mao',
        'book_id': 42,
        'title': 'Little Red Book',
        'publication_date': datetime(1973, 1, 1, 21, 52, 13),
        'keywords': ['Revolution', 'Communism'],
        'phrases': [
            'Revolutionary wars are inevitable in class society',
            'War is the continuation of politics'
        ],
        'age': 24,
        'pages': None
    }
    annotation = Annotated[AnnotatedBook, XMLEntity('Book')]
    config = SerializerConfig(capitalcase, snakecase)

    text = serialize(dct, annotation, config)
    roundtrip = deserialize(text, annotation, config)
    assert dct == roundtrip


class UnannotatedBook(TypedDict, total=False):
    book_id: int
    title: str
    author: str
    publication_date: datetime
    keywords: List[str]
    phrases: List[str]
    age: Optional[Union[datetime, int]]
    pages: Optional[int]


def test_untyped():
    dct: UnannotatedBook = {
        'author': 'Chairman Mao',
        'book_id': 42,
        'title': 'Little Red Book',
        'publication_date': datetime(1973, 1, 1, 21, 52, 13),
        'keywords': ['Revolution', 'Communism'],
        'phrases': [
            'Revolutionary wars are inevitable in class society',
            'War is the continuation of politics'
        ],
        'age': 24,
        'pages': None
    }
    annotation = Annotated[UnannotatedBook, XMLEntity('Book')]
    config = SerializerConfig(capitalcase, snakecase)

    text = serialize(dct, annotation, config)
    roundtrip = deserialize(text, annotation, config)
    assert dct == roundtrip
