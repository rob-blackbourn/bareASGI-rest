"""Type Definitions"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional


TYPE_DEFINITIONS = {
    str: {
        'is_required': True,
        'is_list': False,
        'type': 'string',
        'format': None,
    },
    int: {
        'is_required': True,
        'is_list': False,
        'type': 'integer',
        'format': None,
    },
    float: {
        'is_required': True,
        'is_list': False,
        'type': 'number',
        'format': None,
    },
    Decimal: {
        'is_required': True,
        'is_list': False,
        'type': 'number',
        'format': None,
    },
    datetime: {
        'is_required': True,
        'is_list': False,
        'type': 'string',
        'format': 'date-time',
    },
    Optional[str]: {
        'is_required': False,
        'is_list': False,
        'type': 'string',
        'format': None,
    },
    Optional[int]: {
        'is_required': False,
        'is_list': False,
        'type': 'integer',
        'format': None,
    },
    Optional[float]: {
        'is_required': False,
        'is_list': False,
        'type': 'number',
        'format': None,
    },
    Optional[Decimal]: {
        'is_required': False,
        'is_list': False,
        'type': 'number',
        'format': None,
    },
    Optional[datetime]: {
        'is_required': False,
        'is_list': False,
        'type': 'string',
        'format': 'date-time',
    },
    List[str]: {
        'is_required': False,
        'is_list': True,
        'type': 'string',
        'format': None,
    },
    List[int]: {
        'is_required': False,
        'is_list': True,
        'type': 'integer',
        'format': None,
    },
    List[float]: {
        'is_required': False,
        'is_list': True,
        'type': 'number',
        'format': None,
    },
    List[Decimal]: {
        'is_required': False,
        'is_list': True,
        'type': 'number',
        'format': None,
    },
    List[datetime]: {
        'is_required': False,
        'is_list': True,
        'type': 'string',
        'format': 'date-time',
    }
}
