"""Tests for swagger.py"""

import inspect
from typing import List

from docstring_parser import parse

from bareasgi_rest.swagger.responses import (
    make_swagger_response_schema
)

from .mocks import MockDict


def test_make_swagger_response_schema():
    """Test make_swagger_response_schema"""

    async def func1() -> str:
        """Func1

        Returns:
            str: A string
        """

    sig = inspect.signature(func1)
    docstring = parse(inspect.getdoc(func1))
    response = make_swagger_response_schema(
        sig.return_annotation,
        docstring.returns if docstring else None,
        'multi'
    )
    assert response == {
        'type': 'string',
        'description': 'A string'
    }

    async def func2() -> MockDict:
        pass

    sig = inspect.signature(func2)
    docstring = parse(inspect.getdoc(func2))
    response = make_swagger_response_schema(
        sig.return_annotation,
        docstring.returns if docstring else None,
        'multi'
    )
    assert response == {
        'type': 'object',
        'properties': {
            'argNum1': {
                'name': 'argNum1',
                'description': 'The first arg',
                'type': 'string'
            },
            'argNum2': {
                'name': 'argNum2',
                'description': 'The second arg',
                'type': 'array',
                'collectionFormat': 'multi',
                'items': {
                    'type': 'integer'
                }
            },
            'argNum3': {
                'name': 'argNum3',
                'description': 'The third arg',
                'type': 'string',
                'format': 'date-time'
            },
            'argNum4': {
                'name': 'argNum4',
                'description': "The fourth arg. Defaults to Decimal('1').",
                'type': 'number'
            },
            'argNum5': {
                'name': 'argNum5',
                'description': 'The fifth arg. Defaults to None.',
                'type': 'number'
            }
        }
    }

    async def func3() -> List[MockDict]:
        pass

    sig = inspect.signature(func3)
    docstring = parse(inspect.getdoc(func3))
    response = make_swagger_response_schema(
        sig.return_annotation,
        docstring.returns if docstring else None,
        'multi'
    )
    assert response['type'] == 'array'
