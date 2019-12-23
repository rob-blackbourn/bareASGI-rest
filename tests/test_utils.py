"""Tests for utils.py"""

from datetime import datetime
from decimal import Decimal
import json
import inspect
from typing import Any, Dict, List, Optional

from bareasgi.basic_router.path_definition import PathDefinition

from bareasgi_rest.utils import (
    make_args,
    JSONEncoderEx,
    camelize_object,
    underscore_object
)


def test_make_args():
    """Test for make_args"""
    async def foo(
            arg1: str,
            *,
            arg2: List[int],
            arg3: datetime,
            arg4: Optional[Decimal] = Decimal('1'),
            arg5: Optional[float] = None
    ) -> Dict[str, Any]:
        return {
            'arg1': arg1,
            'arg2': arg2,
            'arg3': arg3,
            'arg4': arg4,
            'arg5': arg5
        }

    foo_sig = inspect.signature(foo)
    foo_matches = {
        'arg1': 'hello'
    }
    foo_query = {
        'arg2': ['1', '2'],
        'arg3': '1967-08-12T00:00:00',
        'arg4': '3.142'
    }
    foo_body = {

    }

    foo_args, foo_kwargs = make_args(foo_sig, foo_matches, foo_query, foo_body)
    assert foo_args == ('hello',)
    assert foo_kwargs == {
        'arg2': [1, 2],
        'arg3': datetime.fromisoformat('1967-08-12T00:00:00'),
        'arg4': Decimal('3.142'),
        'arg5': None
    }


def test_as_datetime():
    """Test for as_datetime"""
    orig = {
        'one': 1,
        'timestamp': datetime(1967, 8, 12, 15, 42, 12),
        'nested': {
            'timestamp': datetime(1967, 8, 12, 15, 42, 12)
        }
    }
    text = json.dumps(orig, cls=JSONEncoderEx)
    roundtrip = json.loads(text)
    assert orig == roundtrip


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
