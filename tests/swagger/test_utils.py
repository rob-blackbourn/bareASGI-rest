"""Tests for swagger.py"""

import inspect

from docstring_parser import parse, Style

from bareasgi_rest.swagger.utils import find_docstring_param

from .mocks import mock_func


def test_find_docstring_param():
    """Test find_docstring_param"""
    docstring = parse(inspect.getdoc(mock_func), Style.auto)
    arg1_param = find_docstring_param('arg_num1', docstring)
    assert arg1_param is not None
    assert arg1_param.arg_name == 'arg_num1'
    assert find_docstring_param('badarg', docstring) is None
