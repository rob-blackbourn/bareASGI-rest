"""Test errors"""

import docstring_parser
from bareasgi_rest.swagger.errors import gather_error_responses


def test_gather_errors():
    """Test for gather_error_responses"""
    docstring_text = """
    Get a book for a given id

    Args:
        book_id (int): The id of the book

    Raises:
        RestError: 404, when a book is not found

    Returns:
        Tuple[int, Optional[Dict[str, Any]]]: The book or nothing
    """
    docstring = docstring_parser.parse(docstring_text)
    error_response = gather_error_responses(docstring.raises)
    assert error_response == {
        404: {
            'description': 'when a book is not found'
        }
    }
