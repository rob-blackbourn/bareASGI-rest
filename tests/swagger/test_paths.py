"""Tests for swagger.py"""

from bareasgi.basic_router.path_definition import PathDefinition

from bareasgi_rest.swagger.paths import make_swagger_path


def test_make_swagger_path():
    """Test make_swagger_path"""
    path = '/api/1/books/{bookId:int}'
    swagger_path = make_swagger_path(PathDefinition(path))
    assert swagger_path == '/api/1/books/{bookId}'
