"""Tests for swagger.py"""

from datetime import datetime
from decimal import Decimal
import inspect
from typing import Any, Dict, List

from docstring_parser import parse, Style

from bareasgi_rest.swagger.utils import _find_docstring_param

from .mocks import mock_func, MockDict


def test_find_docstring_param():
    """Test _find_docstring_param"""
    docstring = parse(inspect.getdoc(mock_func), Style.auto)
    arg1_param = _find_docstring_param('arg_num1', docstring)
    assert arg1_param is not None
    assert arg1_param.arg_name == 'arg_num1'
    assert _find_docstring_param('badarg', docstring) is None
