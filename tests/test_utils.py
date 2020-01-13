"""Tests for utils.py"""

from datetime import datetime
from decimal import Decimal
import inspect
from typing import Any, Dict, List, Optional
try:
    from typing import TypedDict  # type:ignore
except:  # pylint: disable=bare-except
    from typing_extensions import TypedDict

from bareasgi_rest.utils import (
    make_args,
    camelize_object,
    underscore_object
)


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

def test_make_args():
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
        'argNum1': 'hello'
    }
    foo_query = {
        'argNum2': ['1', '2'],
        'argNum3': '1967-08-12T00:00:00Z',
        'argNum4': '3.142'
    }
    foo_body = {
    }

    foo_args, foo_kwargs = make_args(foo_sig, foo_matches, foo_query, foo_body)
    assert foo_args == ('hello',)
    assert foo_kwargs == {
        'arg_num2': [1, 2],
        'arg_num3': datetime.fromisoformat('1967-08-12T00:00:00'),
        'arg_num4': Decimal('3.142'),
        'arg_num5': None
    }

    async def bar(arg_id: int, arg_body: MockDict) -> Optional[MockDict]:
        return None

    bar_matches = {
        'argId': 42
    }
    bar_query = {}
    bar_body = {
        'arg_num1': 'hello',
        'arg_num2': [1, 2],
        'arg_num3': datetime.fromisoformat('1967-08-12T00:00:00'),
        'arg_num4': Decimal('3.142'),
        'arg_num5': None
    }

    bar_sig = inspect.signature(bar)
    bar_args, bar_kwargs = make_args(bar_sig, bar_matches, bar_query, bar_body)
    assert len(bar_args) == 2
    assert len(bar_kwargs) == 0
    assert bar_args[0] == 42
    assert bar_args[1] == {
        'arg_num1': 'hello',
        'arg_num2': [1, 2],
        'arg_num3': datetime.fromisoformat('1967-08-12T00:00:00'),
        'arg_num4': Decimal('3.142'),
        'arg_num5': None
    }


def test_casing():
    """Tests for camelize and underscore"""
    orig_dct = {
        'first_name': 'rob',
        'addresses': [
            {
                'street_name': 'my street'
            },
            {
                'street_name': 'my other street'
            }
        ]
    }
    camel_dct = camelize_object(orig_dct)
    assert camel_dct == {
        'firstName': 'rob',
        'addresses': [
            {
                'streetName': 'my street'
            },
            {
                'streetName': 'my other street'
            }
        ]
    }
    underscore_dct = underscore_object(camel_dct)
    assert underscore_dct == orig_dct
