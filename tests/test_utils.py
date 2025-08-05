"""Tests for utils.py"""

from datetime import datetime
from decimal import Decimal
from functools import partial
import inspect
from typing import Annotated, Any, TypedDict

import pytest
from stringcase import snakecase, camelcase

from jetblack_serialization import DefaultValue, SerializerConfig
from jetblack_serialization.utils import (
    is_value_type,
    is_container_type,
)
from jetblack_serialization.json import (
    from_json_value,
    JSONValue
)
from bareasgi_rest.arg_builder import make_args


class MockDict(TypedDict):
    """A mock typed dict

    Args:
        arg_num1 (str): The first arg
        arg_num2 (List[int]): The second arg
        arg_num3 (datetime): The third arg
        arg_num4 (Decimal | None, optional): The fourth arg. Defaults to Decimal('1').
        arg_num5 (float | None, optional): The fifth arg. Defaults to None.
    """
    arg_num1: str
    arg_num2: list[int]
    arg_num3: datetime
    arg_num4: Annotated[Decimal | None, DefaultValue(Decimal('1'))]
    arg_num5: Annotated[float | None, DefaultValue(None)]


@pytest.mark.asyncio
async def test_make_args1():
    """Test for make_args"""
    async def foo(
            arg_num1: str,
            *,
            arg_num2: list[int],
            arg_num3: datetime,
            arg_num4: Decimal | None = Decimal('1'),
            arg_num5: float | None = None
    ) -> dict[str, Any]:
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
        'arg_num3': ['1967-08-12T00:00:00Z'],
        'arg_num4': ['3.142']
    }

    async def foo_body_reader(annotation: Any) -> Any:
        return {}

    foo_args, foo_kwargs = await make_args(
        foo_sig,
        foo_matches,
        foo_query,
        foo_body_reader,
        partial(
            from_json_value,
            SerializerConfig(
                key_deserializer=snakecase,
                key_serializer=camelcase
            )
        )
    )
    assert foo_args == ('hello',)
    assert foo_kwargs == {
        'arg_num2': [1, 2],
        'arg_num3': datetime.fromisoformat('1967-08-12T00:00:00Z'),
        'arg_num4': Decimal('3.142'),
        'arg_num5': None
    }


@pytest.mark.asyncio
async def test_make_args2() -> None:
    """Test for make_args"""
    async def bar(
            arg_id: int,
            arg_query: str,
            arg_body: Annotated[MockDict, JSONValue()]
    ) -> MockDict | None:
        assert isinstance(arg_id, int)
        assert isinstance(arg_query, str)
        assert isinstance(arg_body, dict)
        return None

    bar_matches: dict[str, Any] = {
        'arg_id': 42
    }
    bar_query = {
        'arg_query': ['query']
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
        partial(
            from_json_value,
            SerializerConfig(
                key_serializer=snakecase,
                key_deserializer=camelcase
            )
        )
    )
    assert len(bar_args) == 3
    assert len(bar_kwargs) == 0
    assert bar_args[0] == 42
    assert bar_args[1] == 'query'
    assert bar_args[2] == {
        'arg_num1': 'hello',
        'arg_num2': [1, 2],
        'arg_num3': datetime.fromisoformat('1967-08-12T00:00:00'),
        'arg_num4': Decimal('3.142'),
        'arg_num5': None
    }


def test_is_json_container():
    """Test is_container_type"""

    def str_func() -> str:
        return "bar"
    str_sig = inspect.signature(str_func)
    assert not is_container_type(str_sig.return_annotation)

    def list_func() -> list[dict[str, Any]]:
        return []
    list_sig = inspect.signature(list_func)
    assert is_container_type(list_sig.return_annotation)

    def dict_func() -> dict[str, Any]:
        return {}
    dict_sig = inspect.signature(dict_func)
    assert is_container_type(dict_sig.return_annotation)

    def typed_dict_func() -> list[dict[str, Any]]:
        return []
    typed_dict_sig = inspect.signature(typed_dict_func)
    assert is_container_type(typed_dict_sig.return_annotation)


def test_is_json_literal():
    """Test is_simple_type"""
    assert is_value_type(str)
    assert is_value_type(int)
    assert is_value_type(float)
    assert is_value_type(Decimal, [Decimal])
    assert is_value_type(datetime, [datetime])
    assert not is_value_type(list[str])
    assert not is_value_type(dict[str, Any])
    assert not is_value_type(MockDict)
