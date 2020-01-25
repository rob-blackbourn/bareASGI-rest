"""Tests for JSON serialization"""

from typing import Any, Dict

from stringcase import snakecase, camelcase

from bareasgi_rest.protocol.json.typed_deserializer import from_json_value


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
