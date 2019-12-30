# bareASGI-rest


This package provides enhanced support for writing REST
APIs with [bareASGI](https://bareasgi.com).

It includes:

* A router to simplify the creation of REST APIs,
* A swagger API endpoint

## Installation

The package can be install from pypi.

It is currently pre-release so you will need the --pre flag.

```bash
$ pip install --pre bareASGI-rest
```

An ASGI server will be required to run the code. The examples below use
[uvicorn](https://www.uvicorn.org/).

```bash
$ pip install uvicorn
```

## Usage

The router provided by this package maps the arguments and
types of request handlers.

We will create a mock book repository.

Here is the type of a book. We use `TypedDict` to allow automatic type discovery

```python
from datetime import datetime
try:
    # Available in 3.8
    from typing import TypedDict  # type:ignore
except:
    # Available in 3.7
    from typing_extensions import TypedDict

class Book(TypedDict):
    """A Book

    Args:
        book_id (int): The book id
        title (str): The title
        author (str): The author
        published (datetime): The publication date
    """
    book_id: int
    title: str
    author: str
    published: datetime
```

Note: the docstring will be used to provide documentation for swagger.

Now we can build the API.

```python
from Typing import Dict, List
from urllib.error import HTTPError


BOOKS: Dict[int, Book]
NEXT_ID: int = 0

async def get_books() -> List[Book]:
    """Get all the books.

    This method gets all the books in the shop.

    Returns:
        List[Book]: All the books
    """
    return list(BOOKS.values())


async def get_book(book_id: int) -> Book:
    """Get a book for a given id

    Args:
        book_id (int): The id of the book

    Raises:
        HTTPError: 404, when a book is not found

    Returns:
        Book: The book
    """

    if book_id not in BOOKS:
        raise HTTPError(None, 404, None, None, None)

    return BOOKS[book_id]


async def create_book(
        author: str,
        title: str,
        published: datetime
) -> int:
    """Add a book

    Args:
        author (str): The author
        title (str): The title
        published (datetime): The publication date

    Returns:
        int: The id of the new book
    """
    NEXT_ID += 1
    BOOKS[NEXT_ID] = Book(
        book_id=NEXT_ID,
        title=title,
        author=author,
        published=published
    )
    return NEXT_ID


async def update_book(
        book_id: int,
        author: str,
        title: str,
        published: datetime
) -> None:
    """Update a book

    Args:
        book_id (int): The id of the book to update
        author (str): The new author
        title (str): The title
        published (datetime): The publication date

    Raises:
        HTTPError: 404, when a book is not found

    Returns:
        Tuple[int, Any]: Nothing
    """
    if book_id not in BOOKS:
        raise HTTPError(None, 404, None, None, None)
    BOOKS[book_id]['title'] = title
    BOOKS[book_id]['author'] = author
    BOOKS[book_id]['published'] = published
```

We can see that errors are handler by raising HTTPError
from the `urllib.errors` standard library package.

Now we must create our application and add support for the router.

```python
from bareasgi_rest import RestHTTPRouter, add_swagger_ui


rest_router = RestHttpRouter(
    None,
    title="Books",
    version="1",
    description="A book api",
    base_path='/api/1',
    tags=[
        {
            'name': 'Books',
            'description': 'The book store API'
        }
    ]
)
app = Application(http_router=rest_router)
add_swagger_ui(app)
```

Note the `base-path` argument can be used to prefix all
paths.

Now we can create the routes:

```python
tags = ['Books']
router.add_rest({'GET'}, '/books', get_books,tags=tags)
router.add_rest({'GET'}, '/books/{bookId:int}', get_book, tags=tags)
router.add_rest({'POST'}, '/books', create_book, tags=tags, status_code=201)
router.add_rest({'PUT'}, '/books/{bookId:int}', update_book, tags=tags, status_code=204)
```

Finally we can serve the API:

```python
uvicorn.run(app, port=9009)
```

Browsing to http://localhost/api/1/swagger we should see:

![Top Level](screenshot1.png)

