"""Tests for utils.py"""

from datetime import datetime
from decimal import Decimal
import inspect
from typing import Any, Dict, List, Optional
try:
    from typing import TypedDict  # type:ignore
except:  # pylint: disable=bare-except
    from typing_extensions import TypedDict

import pytest
from inflection import underscore

from bareasgi_rest.types import Body
from bareasgi_rest.protocol.json import (
    is_json_container,
    is_json_literal,
    from_json_value
)
from bareasgi_rest.arg_builder import make_args
from bareasgi_rest.utils import camelcase


class MockDict(TypedDict):
    """A mock typed dict

    Args:
        arg_num1 (str): The first arg
        arg_num2 (List[int]): The second arg
        arg_num3 (datetime): The third arg
        arg_num4 (Optional[Decimal], optional): The fourth arg. Defaults to Decimal('1').
        arg_num5 (Optional[float], optional): The fifth arg. Defaults to None.
    """
    arg_num1: str
    arg_num2: List[int]
    arg_num3: datetime
    arg_num4: Optional[Decimal] = Decimal('1')
    arg_num5: Optional[float] = None


@pytest.mark.asyncio
async def test_make_args():
    """Test for make_args"""
    async def foo(
            arg_num1: str,
            *,
            arg_num2: List[int],
            arg_num3: datetime,
            arg_num4: Optional[Decimal] = Decimal('1'),
            arg_num5: Optional[float] = None
    ) -> Dict[str, Any]:
        return {
            'arg_num1': arg_num1,
            'arg_num2': arg_num2,
            'arg_num3': arg_num3,
            'arg_num4': arg_num4,
            'arg_num5': arg_num5
        }

    foo_sig = inspect.signature(foo)
    foo_matches = {
        'arg_num1': 'hello'
    }
    foo_query = {
        'arg_num2': ['1', '2'],
        'arg_num3': '1967-08-12T00:00:00Z',
        'arg_num4': '3.142'
    }

    async def foo_body_reader(annotation: Any) -> Any:
        return {}

    foo_args, foo_kwargs = await make_args(
        foo_sig,
        foo_matches,
        foo_query,
        foo_body_reader,
        camelcase
    )
    assert foo_args == ('hello',)
    assert foo_kwargs == {
        'arg_num2': [1, 2],
        'arg_num3': datetime.fromisoformat('1967-08-12T00:00:00'),
        'arg_num4': Decimal('3.142'),
        'arg_num5': None
    }

    async def bar(
            arg_id: int,
            arg_query: str,
            arg_body: Body[MockDict]
    ) -> Optional[MockDict]:
        return None

    bar_matches = {
        'arg_id': 42
    }
    bar_query = {
        'arg_query': 'query'
    }

    async def bar_body_reader(annotation: Any) -> Any:
        return {
            'arg_num1': 'hello',
            'arg_num2': [1, 2],
            'arg_num3': datetime.fromisoformat('1967-08-12T00:00:00'),
            'arg_num4': Decimal('3.142'),
            'arg_num5': None
        }

    bar_sig = inspect.signature(bar)
    bar_args, bar_kwargs = await make_args(
        bar_sig,
        bar_matches,
        bar_query,
        bar_body_reader,
        camelcase
    )
    assert len(bar_args) == 3
    assert len(bar_kwargs) == 0
    assert bar_args[0] == 42
    assert bar_args[1] == 'query'
    assert bar_args[2] == Body({
        'arg_num1': 'hello',
        'arg_num2': [1, 2],
        'arg_num3': datetime.fromisoformat('1967-08-12T00:00:00'),
        'arg_num4': Decimal('3.142'),
        'arg_num5': None
    })


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
