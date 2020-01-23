"""Tests for serialization"""

from datetime import datetime
from typing import List

from typing_extensions import TypedDict, Annotated  # type: ignore

from bareasgi_rest.protocol.xml.deserialization import deserialise_xml
from bareasgi_rest.protocol.xml.annotations import (
    XMLEntity,
    XMLAttribute
)


class Book(TypedDict, total=False):
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


def test_from_xml_element():
    """Test for from_xml_element"""

    text = """
<Book  bookId="42">
    <Title>Little Red Book</Title>
    <Author>Chairman Mao</Author>
    <PublicationDate>1973-01-01T21:52:13Z</PublicationDate>
    <Keywords>
      <Keyword>Revolution</Keyword>
      <Keyword>Communism</Keyword>
    </Keywords>
    <Phrase>Revolutionary wars are inevitable in class society</Phrase>
    <Phrase>War is the continuation of politics</Phrase>
</Book>
"""
    dct = deserialise_xml(
        b'application/xml',
        {},
        text,
        Annotated[Book, XMLEntity("Book")]
    )
    assert dct == {
        'author': 'Chairman Mao',
        'book_id': 42,
        'title': 'Little Red Book',
        'publication_date': datetime(1973, 1, 1, 21, 52, 13),
        'keywords': ['Revolution', 'Communism'],
        'phrases': [
            'Revolutionary wars are inevitable in class society',
            'War is the continuation of politics'
        ]
    }
