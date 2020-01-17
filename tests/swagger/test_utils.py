"""Tests for swagger.py"""

from datetime import datetime
from decimal import Decimal
import inspect
from typing import Any, Dict, List

from docstring_parser import parse, Style

from bareasgi_rest.swagger.utils import (
    _find_docstring_param,
    is_json_container,
    is_json_literal
)

from .mocks import mock_func, MockDict


def test_find_docstring_param():
    """Test _find_docstring_param"""
    docstring = parse(inspect.getdoc(mock_func), Style.auto)
    arg1_param = _find_docstring_param('arg_num1', docstring)
    assert arg1_param is not None
    assert arg1_param.arg_name == 'arg_num1'
    assert _find_docstring_param('badarg', docstring) is None


def test_is_json_container():
    """Test is_json_container"""

    def str_func() -> str:
        pass
    str_sig = inspect.signature(str_func)
    assert not is_json_container(str_sig.return_annotation)

    def list_func() -> List[Dict[str, Any]]:
        pass
    list_sig = inspect.signature(list_func)
    assert is_json_container(list_sig.return_annotation)

    def dict_func() -> Dict[str, Any]:
        pass
    dict_sig = inspect.signature(dict_func)
    assert is_json_container(dict_sig.return_annotation)

    def typed_dict_func() -> List[Dict[str, Any]]:
        pass
    typed_dict_sig = inspect.signature(typed_dict_func)
    assert is_json_container(typed_dict_sig.return_annotation)


def test_is_json_literal():
    """Test is_json_literal"""
    assert is_json_literal(str)
    assert is_json_literal(int)
    assert is_json_literal(float)
    assert is_json_literal(Decimal)
    assert is_json_literal(datetime)
    assert not is_json_literal(List[str])
    assert not is_json_literal(Dict[str, Any])
    assert not is_json_literal(MockDict)
