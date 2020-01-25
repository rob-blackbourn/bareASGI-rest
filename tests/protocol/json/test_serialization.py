"""Tests for JSON serialization"""

from datetime import datetime, timedelta
import json
from typing import Any, Dict

from stringcase import snakecase, camelcase

from bareasgi_rest.protocol.json.serialization import (
    JSONEncoderEx,
    json_to_python,
)
from bareasgi_rest.protocol.json.coercion import from_json_value


def test_json():
    """Test for json_to_python"""
    orig = {
        'one': 1,
        'timestamp': datetime(1967, 8, 12, 15, 42, 12),
        'nested': {
            'timestamp': datetime(1967, 8, 12, 15, 42, 12)
        },
        'duration': timedelta(minutes=12)
    }
    text = json.dumps(orig, cls=JSONEncoderEx)
    roundtrip = json.loads(text, object_hook=json_to_python)
    assert orig == roundtrip


def test_from_json_value():
    """Test for form_json_value"""
    source = {
        'argNum1': 'foo',
        'argNum2': [
            {
                'subArg1': 42,
                200: 'status'
            }
        ]
    }
    result = from_json_value(snakecase, camelcase, source, Dict[str, Any])
    assert result == {
        'arg_num1': 'foo',
        'arg_num2': [
            {
                'sub_arg1': 42,
                200: 'status'
            }
        ]
    }
