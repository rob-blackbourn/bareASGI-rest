import asyncio
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


async def main():

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
        assert annotation is not None
        return {}

    foo_args, foo_kwargs = await make_args(
        foo_sig,
        foo_matches,
        foo_query,
        foo_body_reader,
        lambda json_value, annotation: from_json_value(
            json_value,
            annotation,
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


if __name__ == "__main__":
    asyncio.run(main())
