"""Tests for typing info"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from bareasgi_rest.swagger.type_info import _add_type_info


def test_add_type_info():
    """Test _add_type_info"""
    assert _add_type_info({}, str, 'multi', None) == {'type': 'string'}
    assert _add_type_info({}, int, 'multi', None) == {'type': 'integer'}
    assert _add_type_info({}, float, 'multi', None) == {'type': 'number'}
    assert _add_type_info({}, Decimal, 'multi', None) == {'type': 'number'}
    assert _add_type_info({}, datetime, 'multi', None) == {
        'type': 'string',
        'format': 'date-time'
    }

    assert _add_type_info({}, Optional[str], 'multi', None) == {
        'type': 'string'
    }
    assert _add_type_info({}, Optional[int], 'multi', None) == {
        'type': 'integer'
    }
    assert _add_type_info({}, Optional[float], 'multi', None) == {
        'type': 'number'
    }
    assert _add_type_info({}, Optional[Decimal], 'multi', None) == {
        'type': 'number'
    }
    assert _add_type_info({}, Optional[datetime], 'multi', None) == {
        'type': 'string',
        'format': 'date-time'
    }

    assert _add_type_info({}, List[str], 'multi', None) == {
        'type': 'array',
        'collectionFormat': 'multi',
        'items': {
            'type': 'string'
        }
    }
    assert _add_type_info({}, List[int], 'multi', None) == {
        'type': 'array',
        'collectionFormat': 'multi',
        'items': {
            'type': 'integer'
        }
    }
    assert _add_type_info({}, List[float], 'multi', None) == {
        'type': 'array',
        'collectionFormat': 'multi',
        'items': {
            'type': 'number'
        }
    }
    assert _add_type_info({}, List[Decimal], 'multi', None) == {
        'type': 'array',
        'collectionFormat': 'multi',
        'items': {
            'type': 'number'
        }
    }
    assert _add_type_info({}, List[datetime], 'multi', None) == {
        'type': 'array',
        'collectionFormat': 'multi',
        'items': {
            'type': 'string',
            'format': 'date-time'
        }
    }
