"""Tests for swagger.py"""

from decimal import Decimal
import inspect
from typing import List

from docstring_parser import parse
from bareasgi_rest.swagger.type_info import get_property

from .mocks import MockDict


def test_get_property():
    """Test get_property"""

    async def func1() -> str:
        """Func1

        Returns:
            str: A string
        """

    sig = inspect.signature(func1)
    docstring = parse(inspect.getdoc(func1))
    description = docstring.returns.description if docstring else None
    response = get_property(
        sig.return_annotation,
        None,
        description,
        inspect.Parameter.empty,
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
    description = docstring.returns.description if docstring and docstring.returns else None
    response = get_property(
        sig.return_annotation,
        None,
        description,
        inspect.Parameter.empty,
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
                'type': 'number',
                'default': Decimal('1')
            },
            'argNum5': {
                'name': 'argNum5',
                'description': 'The fifth arg. Defaults to None.',
                'type': 'number',
                'default': None
            }
        }
    }

    async def func3() -> List[MockDict]:
        pass

    sig = inspect.signature(func3)
    docstring = parse(inspect.getdoc(func3))
    description = docstring.returns.description if docstring and docstring.returns else None
    response = get_property(
        sig.return_annotation,
        None,
        description,
        inspect.Parameter.empty,
        'multi'
    )
    assert response['type'] == 'array'
