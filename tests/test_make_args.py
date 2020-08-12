"""Tests for make_args"""

from datetime import datetime
from decimal import Decimal
from functools import partial
import inspect
from typing import Any, Dict, List, Optional

import pytest
from stringcase import snakecase, camelcase

from jetblack_serialization.config import SerializerConfig
from jetblack_serialization.json import (
    from_json_value
)
from bareasgi_rest.arg_builder import make_args


@pytest.mark.asyncio
async def test_make_args1():
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
        partial(from_json_value, SerializerConfig(snakecase, camelcase))
    )
    assert foo_args == ('hello',)
    assert foo_kwargs == {
        'arg_num2': [1, 2],
        'arg_num3': datetime.fromisoformat('1967-08-12T00:00:00'),
        'arg_num4': Decimal('3.142'),
        'arg_num5': None
    }
