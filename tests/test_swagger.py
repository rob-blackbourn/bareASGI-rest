"""Tests for swagger.py"""

from datetime import datetime
from decimal import Decimal
import inspect
from typing import Any, Dict, List, Optional

from bareasgi.basic_router.path_definition import PathDefinition

from docstring_parser import parse, Style

from bareasgi_rest.swagger import (
    make_swagger_path,
    _make_swagger_parameter,
    _find_docstring_param,
    _make_swagger_schema,
    make_swagger_parameters
)


async def mock_func(
        arg1: str,
        *,
        arg2: List[int],
        arg3: datetime,
        arg4: Optional[Decimal] = Decimal('1'),
        arg5: Optional[float] = None
) -> Dict[str, Any]:
    """A mock function

    A function to use in tests

    Args:
        arg1 (str): The first arg
        arg2 (List[int]): The second arg
        arg3 (datetime): The third arg
        arg4 (Optional[Decimal], optional): The fourth arg. Defaults to Decimal('1').
        arg5 (Optional[float], optional): The fifth arg. Defaults to None.

    Raises:
        ValueError: It doesn't actually raise this error

    Returns:
        Dict[str, Any]: The args as a dictionary
    """
    return {
        'arg1': arg1,
        'arg2': arg2,
        'arg3': arg3,
        'arg4': arg4,
        'arg5': arg5
    }


def test_make_swagger_path():
    """Test make_swagger_path"""
    path = '/api/1/books/{bookId:int}'
    swagger_path = make_swagger_path(PathDefinition(path))
    assert swagger_path == '/api/1/books/{bookId}'


def test_find_docstring_param():
    """Test _find_docstring_param"""
    docstring = parse(inspect.getdoc(mock_func), Style.auto)
    arg1_param = _find_docstring_param('arg1', docstring)
    assert arg1_param is not None
    assert arg1_param.arg_name == 'arg1'
    assert _find_docstring_param('badarg', docstring) is None


def test_make_swagger_parameter():
    """Test _make_swagger_parameter"""
    sig = inspect.signature(mock_func)
    docstring = parse(inspect.getdoc(mock_func), Style.auto)
    param = _make_swagger_parameter(
        'path',
        sig.parameters['arg1'],
        'multi',
        docstring.params[0]
    )
    assert param == {
        'in': 'path',
        'name': 'arg1',
        'description': 'The first arg',
        'required': True,
        'type': 'string'
    }
    param = _make_swagger_parameter(
        'query',
        sig.parameters['arg2'],
        'multi',
        docstring.params[1]
    )
    assert param == {
        'in': 'query',
        'name': 'arg2',
        'description': 'The second arg',
        'required': False,
        'type': 'array',
        'collectionFormat': 'multi',
        'items': {
            'type': 'integer'
        }
    }
    param = _make_swagger_parameter(
        'query',
        sig.parameters['arg3'],
        'multi',
        docstring.params[2]
    )
    assert param == {
        'in': 'query',
        'name': 'arg3',
        'description': 'The third arg',
        'required': True,
        'type': 'string',
        'format': 'date'
    }
    param = _make_swagger_parameter(
        'query',
        sig.parameters['arg4'],
        'multi',
        docstring.params[3]
    )
    assert param == {
        'in': 'query',
        'name': 'arg4',
        'description': "The fourth arg. Defaults to Decimal('1').",
        'required': False,
        'type': 'number',
        'default': Decimal('1')
    }
    param = _make_swagger_parameter(
        'query',
        sig.parameters['arg5'],
        'multi',
        docstring.params[4]
    )
    assert param == {
        'in': 'query',
        'name': 'arg5',
        'description': 'The fifth arg. Defaults to None.',
        'required': False,
        'type': 'number',
        'default': None
    }


def test_make_swagger_schema():
    """Test for _make_swagger_schema"""
    sig = inspect.signature(mock_func)
    docstring = parse(inspect.getdoc(mock_func), Style.auto)
    params = [
        (param, _find_docstring_param(param.name, docstring))
        for param in sig.parameters.values()
    ]
    schema = _make_swagger_schema(params, 'multi')
    assert schema == {
        'type': 'object',
        'required': [
            'arg1',
            'arg3'
        ],
        'properties': {
            'arg1': {
                'name': 'arg1',
                'description': 'The first arg',
                'type': 'string'
            },
            'arg2': {
                'name': 'arg2',
                'description': 'The second arg',
                'type': 'array',
                'collectionFormat': 'multi',
                'items': {
                    'type': 'integer'
                }
            },
            'arg3': {
                'name': 'arg3',
                'description': 'The third arg',
                'type': 'string',
                'format': 'date'
            },
            'arg4': {
                'name': 'arg4',
                'description': "The fourth arg. Defaults to Decimal('1').",
                'type': 'number',
                'default': Decimal('1')
            },
            'arg5': {
                'name': 'arg5',
                'description': 'The fifth arg. Defaults to None.',
                'type': 'number',
                'default': None
            }
        },
    }


def test_swagger_params():
    """Test for make_swagger_parameters"""
    sig = inspect.signature(mock_func)
    docstring = parse(inspect.getdoc(mock_func), Style.auto)
    accept = b'application/json'
    path_definition = PathDefinition('/foo/bar/{arg1:str}')
    collection_format = 'multi'
    get_params = make_swagger_parameters(
        'GET',
        accept,
        path_definition,
        sig,
        docstring,
        collection_format
    )
    assert get_params == [
        {
            'name': 'arg1',
            'type': 'string',
            'in': 'path',
            'required': True,
            'description': 'The first arg'
        },
        {
            'name': 'arg1',
            'type': 'string',
            'in': 'query',
            'required': True,
            'description': 'The first arg'
        },
        {
            'name': 'arg2',
            'type': 'array',
            'collectionFormat': 'multi',
            'items': {
                'type': 'integer'
            },
            'in': 'query',
            'required': True,
            'description': 'The second arg'
        },
        {
            'name': 'arg3',
            'type': 'string',
            'format': 'date',
            'in': 'query',
            'required': True,
            'description': 'The third arg'
        },
        {
            'name': 'arg4',
            'type': 'number',
            'in': 'query',
            'required': False,
            'default': Decimal('1'),
            'description': "The fourth arg. Defaults to Decimal('1')."
        },
        {
            'name': 'arg5',
            'type': 'number',
            'in': 'query',
            'required': False,
            'default': None,
            'description': 'The fifth arg. Defaults to None.'
        }
    ]
