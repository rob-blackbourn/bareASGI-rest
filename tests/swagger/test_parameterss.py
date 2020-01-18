"""Tests for swagger.py"""

from decimal import Decimal
import inspect

from bareasgi.basic_router.path_definition import PathDefinition
from docstring_parser import parse, Style
from inflection import camelize

from bareasgi_rest.swagger.parameters import (
    _make_swagger_parameter,
    make_swagger_parameters,
    _make_swagger_schema,
)

from bareasgi_rest.swagger.utils import (
    _find_docstring_param,
)

from .mocks import mock_func


def test_make_swagger_parameter():
    """Test _make_swagger_parameter"""
    sig = inspect.signature(mock_func)
    docstring = parse(inspect.getdoc(mock_func), Style.auto)
    param = _make_swagger_parameter(
        'path',
        sig.parameters['arg_num1'],
        'multi',
        docstring.params[0]
    )
    assert param == {
        'in': 'path',
        'name': 'argNum1',
        'description': 'The first arg',
        'required': True,
        'type': 'string'
    }
    param = _make_swagger_parameter(
        'query',
        sig.parameters['arg_num2'],
        'multi',
        docstring.params[1]
    )
    assert param == {
        'in': 'query',
        'name': 'argNum2',
        'description': 'The second arg',
        'required': True,
        'type': 'array',
        'collectionFormat': 'multi',
        'items': {
            'type': 'integer'
        }
    }
    param = _make_swagger_parameter(
        'query',
        sig.parameters['arg_num3'],
        'multi',
        docstring.params[2]
    )
    assert param == {
        'in': 'query',
        'name': 'argNum3',
        'description': 'The third arg',
        'required': True,
        'type': 'string',
        'format': 'date-time'
    }
    param = _make_swagger_parameter(
        'query',
        sig.parameters['arg_num4'],
        'multi',
        docstring.params[3]
    )
    assert param == {
        'in': 'query',
        'name': 'argNum4',
        'description': "The fourth arg. Defaults to Decimal('1').",
        'required': False,
        'type': 'number',
        'default': Decimal('1')
    }
    param = _make_swagger_parameter(
        'query',
        sig.parameters['arg_num5'],
        'multi',
        docstring.params[4]
    )
    assert param == {
        'in': 'query',
        'name': 'argNum5',
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
        (camelize(param.name, False), param,
         _find_docstring_param(param.name, docstring))
        for param in sig.parameters.values()
    ]
    schema = _make_swagger_schema(params, 'multi')
    assert schema == {
        'type': 'object',
        'required': [
            'argNum1',
            'argNum2',
            'argNum3'
        ],
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
        },
    }


def test_swagger_params_get():
    """Test for make_swagger_parameters"""
    sig = inspect.signature(mock_func)
    docstring = parse(inspect.getdoc(mock_func), Style.auto)
    accept = b'application/json'
    path_definition = PathDefinition('/foo/bar/{argNum1:str}')
    collection_format = 'multi'
    get_params = make_swagger_parameters(
        'GET',
        accept,
        path_definition,
        sig.parameters,
        docstring,
        collection_format
    )
    assert get_params == [
        {
            'name': 'argNum1',
            'type': 'string',
            'in': 'path',
            'required': True,
            'description': 'The first arg'
        },
        {
            'name': 'argNum2',
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
            'name': 'argNum3',
            'type': 'string',
            'format': 'date-time',
            'in': 'query',
            'required': True,
            'description': 'The third arg'
        },
        {
            'name': 'argNum4',
            'type': 'number',
            'in': 'query',
            'required': False,
            'default': Decimal('1'),
            'description': "The fourth arg. Defaults to Decimal('1')."
        },
        {
            'name': 'argNum5',
            'type': 'number',
            'in': 'query',
            'required': False,
            'default': None,
            'description': 'The fifth arg. Defaults to None.'
        }
    ]


def test_swagger_params_form():
    """Test for make_swagger_parameters"""
    sig = inspect.signature(mock_func)
    docstring = parse(inspect.getdoc(mock_func), Style.auto)
    accept = b'application/x-www-form-urlencoded'
    path_definition = PathDefinition('/foo/bar/{argNum1:str}')
    collection_format = 'multi'
    get_params = make_swagger_parameters(
        'POST',
        accept,
        path_definition,
        sig.parameters,
        docstring,
        collection_format
    )
    assert get_params == [
        {
            'name': 'argNum1',
            'type': 'string',
            'in': 'path',
            'required': True,
            'description': 'The first arg'
        },
        {
            'name': 'argNum2',
            'type': 'array',
            'collectionFormat': 'multi',
            'items': {
                'type': 'integer'
            },
            'in': 'formData',
            'required': True,
            'description': 'The second arg'
        },
        {
            'name': 'argNum3',
            'type': 'string',
            'format': 'date-time',
            'in': 'formData',
            'required': True,
            'description': 'The third arg'
        },
        {
            'name': 'argNum4',
            'type': 'number',
            'in': 'formData',
            'required': False,
            'default': Decimal('1'),
            'description': "The fourth arg. Defaults to Decimal('1')."
        },
        {
            'name': 'argNum5',
            'type': 'number',
            'in': 'formData',
            'required': False,
            'default': None,
            'description': 'The fifth arg. Defaults to None.'
        }
    ]


def test_swagger_params_body():
    """Test for make_swagger_parameters"""
    sig = inspect.signature(mock_func)
    docstring = parse(inspect.getdoc(mock_func), Style.auto)
    accept = b'application/json'
    path_definition = PathDefinition('/foo/bar/{argNum1:str}')
    collection_format = 'multi'
    get_params = make_swagger_parameters(
        'POST',
        accept,
        path_definition,
        sig.parameters,
        docstring,
        collection_format
    )
    assert get_params == [
        {
            'name': 'argNum1',
            'type': 'string',
            'in': 'path',
            'required': True,
            'description': 'The first arg'
        },
        {
            'in': 'body',
            'name': 'schema',
            'description': 'The body schema',
            'schema': {
                'type': 'object',
                'required': [
                    'argNum2',
                    'argNum3'
                ],
                'properties': {
                    'argNum2': {
                        'name': 'argNum2',
                        'type': 'array',
                        'collectionFormat': 'multi',
                        'items': {
                            'type': 'integer'
                        },
                        'description': 'The second arg'
                    },
                    'argNum3': {
                        'name': 'argNum3',
                        'type': 'string',
                        'format': 'date-time',
                        'description': 'The third arg'
                    },
                    'argNum4': {
                        'name': 'argNum4',
                        'type': 'number',
                        'default': Decimal('1'),
                        'description': "The fourth arg. Defaults to Decimal('1')."
                    },
                    'argNum5': {
                        'name': 'argNum5',
                        'type': 'number',
                        'default': None,
                        'description': 'The fifth arg. Defaults to None.'
                    }
                }
            }
        }
    ]
