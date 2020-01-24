"""Tests for JSON serialization"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from typing_extensions import TypedDict, Annotated  # type: ignore

from bareasgi_rest.protocol.json.deserializer import deserialize
from bareasgi_rest.protocol.json.annotations import (
    JSONAnnotation,
    JSONValue,
    JSONList,
    JSONObject,
    JSONProperty,
    is_json_annotation,
    get_json_annotation
)


class Book(TypedDict, total=False):
    book_id: Annotated[int, JSONProperty("bookId")]
    title: Annotated[str, JSONProperty("title")]
    author: Annotated[str, JSONProperty("author")]
    publication_date: Annotated[datetime, JSONProperty("publicationDate")]
    keywords: Annotated[List[Annotated[str, JSONValue()]],
                        JSONList("keywords")]
    phrases: Annotated[List[Annotated[str, JSONValue()]], JSONList("phrases")]
    age: Annotated[Optional[Union[datetime, int]], JSONProperty("age")]
    pages: Annotated[Optional[int], JSONProperty("pages")]


def test_deserialize():
    """Test for deserialize"""

    text = """
{
    "bookId": 42,
    "title": "Little Red Book",
    "author": "Chairman Mao",
    "publicationDate": "1973-01-01T21:52:13Z",
    "keywords": [
      "Revolution",
      "Communism"
    ],
    "phrases": [
        "Revolutionary wars are inevitable in class society",
        "War is the continuation of politics"
    ],
    "age": 24
}
"""
    dct = deserialize(
        text,
        Annotated[Book, JSONValue()]
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
        ],
        'age': 24,
        'pages': None
    }
